# pages/01_集計.py
import streamlit as st
import pandas as pd

from lib_db import (
    get_conn, inject_css, read_df_sql, get_score_red_blue,
    POINT_MAP, STAT_SET, FOUL_SET
)

from app_auth import require_login, render_userbox


# set_page_config はできるだけ先頭で実行
try:
    st.set_page_config(
        page_title="📊 SCORE TALLY",
        page_icon="📊",
        layout="centered",
        initial_sidebar_state="expanded",
    )
except Exception:
    pass


# 認証
require_login()

try:
    render_userbox(key="logout_button_agg")
except TypeError:
    render_userbox()


# 共通CSS
inject_css()

# 集計画面用CSS
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 45%, #e0f2fe 100%);
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

.page-hero {
    text-align: center;
    padding: 18px 8px 10px;
}

.page-title {
    font-size: 38px;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 6px;
}

.page-subtitle {
    color: #64748b;
    font-size: 15px;
}

.scorebar {
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 24px;
    padding: 22px 24px;
    margin: 18px 0 22px;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.10);
}

.scorebox {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

.info {
    font-size: 15px;
    color: #64748b;
    font-weight: 800;
    letter-spacing: 0.08em;
}

.scorechip {
    display: inline-block;
    padding: 12px 22px;
    border-radius: 999px;
    font-size: 24px;
    font-weight: 900;
    margin: 4px;
    color: white;
}

.scorechip.red {
    background: linear-gradient(135deg, #ef4444, #f97316);
    box-shadow: 0 10px 24px rgba(239, 68, 68, 0.25);
}

.scorechip.blue {
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
}

.section-card {
    background: rgba(255,255,255,0.94);
    padding: 22px 24px;
    border-radius: 22px;
    border: 1px solid rgba(148, 163, 184, 0.25);
    box-shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
    margin: 16px 0;
}

h2, h3 {
    color: #0f172a;
}

[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
}

div.stButton > button {
    width: 100%;
    border-radius: 999px;
    height: 44px;
    font-weight: 800;
    border: none;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: white;
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
}

div.stButton > button:hover {
    transform: translateY(-1px);
    color: white;
    box-shadow: 0 14px 28px rgba(37, 99, 235, 0.32);
}

div[data-testid="stPageLink"] a {
    border-radius: 999px;
    font-weight: 800;
}

div[data-testid="stTabs"] button {
    font-weight: 800;
    font-size: 15px;
}

div[data-baseweb="tab-list"] {
    gap: 8px;
}

div[data-baseweb="tab"] {
    background: rgba(255,255,255,0.75);
    border-radius: 999px;
    padding: 8px 18px;
}

.empty-card {
    background: rgba(255,255,255,0.95);
    padding: 28px 24px;
    border-radius: 24px;
    text-align: center;
    border: 1px solid rgba(148, 163, 184, 0.25);
    box-shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
}
</style>
""", unsafe_allow_html=True)


conn = get_conn()


def render_back_to_main():
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        if hasattr(st, "page_link"):
            st.page_link(
                "main.py",
                label="⬅️ main画面へ戻る",
                icon="🏠",
                width="stretch",
            )
        else:
            if st.button("⬅️ main画面へ戻る", width="stretch"):
                try:
                    st.switch_page("main.py")
                except Exception:
                    st.experimental_set_query_params()
                    st.experimental_rerun()


st.markdown("""
<div class="page-hero">
    <div class="page-title">📊 SCORE TALLY</div>
    <div class="page-subtitle">得点・スタッツ・反則をまとめて確認できます</div>
</div>
""", unsafe_allow_html=True)


# 再集計案内
if "agg_refresh_key" in st.session_state:
    try:
        st.toast("♻️ 集計しました", icon="♻️")
    except Exception:
        st.success("集計しました")
    del st.session_state["agg_refresh_key"]


# 固定バー（全体スコア）
red_pts, blue_pts = get_score_red_blue(conn)

st.markdown(f"""
<div class="scorebar">
  <div class="scorebox">
    <div class="info">📊 TOTAL SCORE</div>
    <div>
      <span class="scorechip red">Red: {red_pts}</span>
      <span class="scorechip blue">Blue: {blue_pts}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


df = read_df_sql(conn)

if df.empty:
    st.markdown("""
    <div class="empty-card">
        <h3>📭 集計対象データがありません</h3>
        <p>スコア入力後に、この画面で集計結果を確認できます。</p>
    </div>
    """, unsafe_allow_html=True)

    render_back_to_main()
    st.stop()


# 前処理
score_df = df[df["得点・アシスト"].isin(POINT_MAP.keys())].copy()
if not score_df.empty:
    score_df["得点"] = score_df["得点・アシスト"].map(POINT_MAP)

stat_df = (
    df[df["得点・アシスト"].isin(STAT_SET)]
    .copy()
    .rename(columns={"得点・アシスト": "項目"})
    .assign(回数=1)
)

foul_df = (
    df[df["得点・アシスト"].isin(FOUL_SET)]
    .copy()
    .rename(columns={"得点・アシスト": "項目"})
    .assign(回数=1)
)


tab_score, tab_stat, tab_foul = st.tabs(["🧮 得点", "📈 スタッツ", "🚨 反則"])


with tab_score:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📌 TEAMごとの得点")
    st.dataframe(
        score_df.groupby("TEAM", as_index=False)["得点"].sum()
        if not score_df.empty else pd.DataFrame({"TEAM": [], "得点": []}),
        width="stretch",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🚀 CLASSごとの得点")
    st.dataframe(
        score_df.groupby(["CLASS", "TEAM"], as_index=False)["得点"].sum()
        if not score_df.empty else pd.DataFrame({"CLASS": [], "TEAM": [], "得点": []}),
        width="stretch",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("⏱️ CLASS × QUARTERごとの得点")

    if not score_df.empty:
        pivot = pd.pivot_table(
            score_df,
            index=["CLASS", "クォーター"],
            columns="TEAM",
            values="得点",
            aggfunc="sum",
            fill_value=0,
        )

        if {"Red", "Blue"}.issubset(set(pivot.columns)):
            pivot["合計"] = pivot["Red"] + pivot["Blue"]

        st.dataframe(pivot.reset_index(), width="stretch")
    else:
        st.info("得点データがありません。")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🏅 得点ランキング")
    N = st.number_input(
        "得点ランキング",
        min_value=1,
        max_value=500,
        value=10,
        step=1,
        key="topN_all",
    )

    if not score_df.empty:
        per_player_all = (
            score_df.groupby(["CLASS", "TEAM", "ビブスType", "背番号", "名前"], as_index=False)["得点"]
            .sum()
            .sort_values(["得点", "CLASS", "TEAM", "背番号"], ascending=[False, True, True, True])
            .head(int(N))
        )
        st.dataframe(per_player_all, width="stretch")
    else:
        st.info("得点ランキングのデータがありません。")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🏅 得点ランキング CLASS × TEAM")

    col_sel1, col_sel2, col_sel3 = st.columns([1, 1, 1])

    with col_sel1:
        sel_cls = st.selectbox("CLASS", ("初級", "中級", "上級"), key="cls_pick_for_topN")

    with col_sel2:
        sel_team = st.selectbox("TEAM", ("すべて", "Red", "Blue"), key="team_pick_for_topN")

    with col_sel3:
        N_cls = st.number_input(
            "上位N",
            min_value=1,
            max_value=500,
            value=10,
            step=1,
            key="topN_cls",
        )

    subset = score_df[score_df["CLASS"] == sel_cls].copy()

    if sel_team != "すべて":
        subset = subset[subset["TEAM"] == sel_team]

    if subset.empty:
        if sel_team == "すべて":
            st.info(f"{sel_cls} の得点データがありません。")
        else:
            st.info(f"{sel_cls} / {sel_team} の得点データがありません。")
    else:
        per_player_cls = (
            subset.groupby(["TEAM", "ビブスType", "背番号", "名前"], as_index=False)["得点"]
            .sum()
            .sort_values(["得点", "TEAM", "背番号"], ascending=[False, True, True])
            .head(int(N_cls))
        )
        st.dataframe(per_player_cls, width="stretch")

    st.markdown("</div>", unsafe_allow_html=True)


with tab_stat:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📌 TEAM")

    if not stat_df.empty:
        st.dataframe(
            stat_df.groupby(["TEAM", "項目"], as_index=False)["回数"].sum(),
            width="stretch",
        )
    else:
        st.info("スタッツのデータがありません。")

    st.markdown("</div>", unsafe_allow_html=True)

    if not stat_df.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🚀 CLASSごとのスタッツ")
        st.dataframe(
            stat_df.groupby(["CLASS", "TEAM", "項目"], as_index=False)["回数"].sum(),
            width="stretch",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("⛹️‍♂️ 選手ごとのスタッツ")

        class_opts = sorted(stat_df["CLASS"].dropna().unique().tolist())
        sel_cls = st.selectbox("CLASS を選択", class_opts, key="stat_cls_pick_for_players")

        cls_df = stat_df[stat_df["CLASS"] == sel_cls]

        if cls_df.empty:
            st.info(f"{sel_cls} のスタッツがありません。")
        else:
            st.dataframe(
                cls_df.groupby(["TEAM", "ビブスType", "背番号", "名前", "項目"], as_index=False)["回数"]
                .sum()
                .sort_values(["TEAM", "背番号", "名前", "項目"]),
                width="stretch",
            )

        st.markdown("</div>", unsafe_allow_html=True)


with tab_foul:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🚨 反則の集計")

    if foul_df.empty:
        st.info("反則のデータがありません。")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        scope_opts = ["ファールのみ", "ターンオーバーのみ"]

        prev = st.session_state.get("foul_scope_radio", "ファールのみ")
        if prev not in scope_opts:
            prev = "ファールのみ"

        scope = st.radio(
            "対象",
            scope_opts,
            horizontal=True,
            index=scope_opts.index(prev),
            key="foul_scope_radio",
            label_visibility="collapsed",
        )

        if scope == "ファールのみ":
            sub = foul_df[foul_df["項目"] == "ファール"].copy()
            scope_tag = "（ファールのみ）"
        else:
            sub = foul_df[foul_df["項目"] == "ターンオーバー"].copy()
            scope_tag = "（ターンオーバーのみ）"

        if sub.empty:
            st.info(f"選択中の範囲 {scope_tag} にデータがありません。")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.subheader(f"📌 TEAM {scope_tag}")
            st.dataframe(
                sub.groupby(["TEAM", "項目"], as_index=False)["回数"]
                .sum()
                .sort_values(["TEAM", "項目"]),
                width="stretch",
            )

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader(f"🚀 CLASSごとの反則 {scope_tag}")
            st.dataframe(
                sub.groupby(["CLASS", "TEAM", "項目"], as_index=False)["回数"]
                .sum()
                .sort_values(["CLASS", "TEAM", "項目"]),
                width="stretch",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader(f"🚀⏱️ CLASS × クォーターごとの反則 {scope_tag}")
            st.dataframe(
                sub.groupby(["クォーター", "TEAM", "項目"], as_index=False)["回数"]
                .sum()
                .sort_values(["クォーター", "TEAM", "項目"]),
                width="stretch",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader(f"⛹️‍♀️ 選手ごとの反則（CLASSを選択）{scope_tag}")

            class_opts = sorted(sub["CLASS"].dropna().unique().tolist())
            sel_cls_foul = st.selectbox(
                "CLASS を選択",
                class_opts,
                key="foul_cls_pick_for_players",
            )

            cls_foul = sub[sub["CLASS"] == sel_cls_foul]

            if cls_foul.empty:
                st.info(f"{sel_cls_foul} のデータがありません。")
            else:
                st.dataframe(
                    cls_foul.groupby(["TEAM", "ビブスType", "背番号", "名前", "項目"], as_index=False)["回数"]
                    .sum()
                    .sort_values(["TEAM", "背番号", "名前", "項目"]),
                    width="stretch",
                )

            st.markdown("</div>", unsafe_allow_html=True)


render_back_to_main()