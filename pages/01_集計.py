# pages/01_集計.py
import streamlit as st
import pandas as pd
import time as _t
import streamlit as st
import streamlit.components.v1 as components

from lib_db import (
    get_conn, inject_css, read_df_sql, get_score_red_blue,
    POINT_MAP, STAT_SET, FOUL_SET
)

st.set_page_config(page_title="📊 集計ページ", layout="centered", initial_sidebar_state="expanded")
inject_css()
conn = get_conn()
        
st.title("📊 集計（全データ）")

# ♻️ 再集計案内（ページ実行でDB読み直し＝再集計）
if "agg_refresh_key" in st.session_state:
    try:
        st.toast("♻️ 集計しました（最新データで表示）", icon="♻️")
    except Exception:
        st.success("集計しました（最新データで表示）")
    del st.session_state["agg_refresh_key"]

# ─────────────────────────────────────────
# ⬅️ スコア画面
# ─────────────────────────────────────────

# 固定バー（全体スコア）
red_pts, blue_pts = get_score_red_blue(conn)
st.markdown(f"""
<div class="scorebar">
  <div class="scorebox">
    <div class="info">📊 全データ合計スコア</div>
    <div>
      <span class="scorechip red">Red: {red_pts}</span>
      <span class="scorechip blue">Blue: {blue_pts}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

df = read_df_sql(conn)
if df.empty:
    st.info("集計対象データがありません。"); st.stop()

# 前処理
score_df = df[df['得点・アシスト'].isin(POINT_MAP.keys())].copy()
if not score_df.empty:
    score_df['得点'] = score_df['得点・アシスト'].map(POINT_MAP)

stat_df = df[df['得点・アシスト'].isin(STAT_SET)].copy().rename(columns={'得点・アシスト':'項目'}).assign(回数=1)
foul_df = df[df['得点・アシスト'].isin(FOUL_SET)].copy().rename(columns={'得点・アシスト':'項目'}).assign(回数=1)

tab_score, tab_stat, tab_foul = st.tabs(["🧮 得点", "📈 スタッツ", "🚨 反則"])

with tab_score:
    st.subheader('📌 TEAMごとの得点（全体）')
    st.dataframe(
        score_df.groupby('TEAM', as_index=False)['得点'].sum()
        if not score_df.empty else pd.DataFrame({'TEAM': [], '得点': []}),
        use_container_width=True
    )

    st.subheader('📌 CLASS × TEAM ごとの得点（全体）')
    st.dataframe(
        score_df.groupby(['CLASS','TEAM'], as_index=False)['得点'].sum()
        if not score_df.empty else pd.DataFrame({'CLASS': [], 'TEAM': [], '得点': []}),
        use_container_width=True
    )

    st.subheader('⏱️🎓 CLASS × クォーター × TEAM（クロス集計）')
    pivot = pd.pivot_table(
        score_df, index=['CLASS','クォーター'], columns='TEAM',
        values='得点', aggfunc='sum', fill_value=0
    )
    if {'Red','Blue'}.issubset(set(pivot.columns)):
        pivot['合計'] = pivot['Red'] + pivot['Blue']
    st.dataframe(pivot.reset_index(), use_container_width=True)

    st.subheader('🏅 上位N人（全体）')
    N = st.number_input("上位N（全体）", min_value=1, max_value=500, value=10, step=1, key="topN_all")
    per_player_all = (
        score_df.groupby(['CLASS','TEAM','ビブスType','背番号','名前'], as_index=False)['得点']
        .sum()
        .sort_values(['得点','CLASS','TEAM','背番号'], ascending=[False, True, True, True])
        .head(int(N))
    )
    st.dataframe(per_player_all, use_container_width=True)

    st.subheader('🏅 CLASS別：上位N人（ランキング）')
    sel_cls = st.selectbox('CLASS を選択', ('初級','中級','上級'), key='cls_pick_for_topN')
    N_cls = st.number_input("上位N（選択CLASS）", min_value=1, max_value=500, value=10, step=1, key="topN_cls")
    cls_df = score_df[score_df['CLASS'] == sel_cls]
    if cls_df.empty:
        st.info(f'{sel_cls} の得点データがありません。')
    else:
        per_player_cls = (
            cls_df.groupby(['TEAM','ビブスType','背番号','名前'], as_index=False)['得点']
            .sum()
            .sort_values(['得点','TEAM','背番号'], ascending=[False, True, True])
            .head(int(N_cls))
        )
        st.dataframe(per_player_cls, use_container_width=True)

with tab_stat:
    st.subheader('📌 TEAM × 項目（全体）')
    if not stat_df.empty:
        # 既存
        st.dataframe(
            stat_df.groupby(['TEAM','項目'], as_index=False)['回数'].sum(),
            use_container_width=True
        )

        # ① CLASS × TEAM ごとのスタッツ（項目別）
        st.subheader('🎓 CLASS × TEAM × 項目（全体）')
        st.dataframe(
            stat_df.groupby(['CLASS','TEAM','項目'], as_index=False)['回数'].sum(),
            use_container_width=True
        )

        # ② CLASS × クォーター × TEAM のスタッツ（項目別）
        st.subheader('⏱️🎓 CLASS × クォーター × TEAM × 項目（全体）')
        st.dataframe(
            stat_df.groupby(['CLASS','クォーター','TEAM','項目'], as_index=False)['回数'].sum()
                    .sort_values(['CLASS','クォーター','TEAM','項目']),
            use_container_width=True
        )

        # ③ 選手 × 項目（CLASS選択）
        st.subheader('🙋‍♀️ 選手 × 項目（CLASSを選択）')
        class_opts = sorted(stat_df['CLASS'].dropna().unique().tolist())
        sel_cls = st.selectbox('CLASS を選択', class_opts, key='stat_cls_pick_for_players')

        cls_df = stat_df[stat_df['CLASS'] == sel_cls]
        if cls_df.empty:
            st.info(f'{sel_cls} のスタッツがありません。')
        else:
            st.dataframe(
                cls_df.groupby(['TEAM','ビブスType','背番号','名前','項目'], as_index=False)['回数'].sum()
                      .sort_values(['TEAM','背番号','名前','項目']),
                use_container_width=True
            )

    else:
        st.info('スタッツのデータがありません。')

with tab_foul:
    st.subheader('📌 反則の集計')

    if foul_df.empty:
        st.info('反則のデータがありません。')
    else:
        # 既定値をセッションに用意（初回のみ）
        st.session_state.setdefault("foul_scope_radio", "全体")

        scope_opts = ["全体", "ファールのみ", "ターンオーバーのみ"]
        # 直前の選択を維持して表示
        scope = st.radio(
            "対象",
            scope_opts,
            horizontal=True,
            index=scope_opts.index(st.session_state["foul_scope_radio"]),
            key="foul_scope_radio",
            label_visibility="collapsed",
        )
        # ← ここでの手動代入は不要です（この行は削除）
        # st.session_state["foul_scope_radio"] = scope

        if scope == "ファールのみ":
            sub = foul_df[foul_df["項目"] == "ファール"].copy()
            scope_tag = "（ファールのみ）"
        elif scope == "ターンオーバーのみ":
            sub = foul_df[foul_df["項目"] == "ターンオーバー"].copy()
            scope_tag = "（ターンオーバーのみ）"
        else:
            sub = foul_df.copy()
            scope_tag = "（全体）"

        if sub.empty:
            st.info(f"選択中の範囲 {scope_tag} にデータがありません。")
        else:
            st.subheader(f'📌 TEAM × 項目 {scope_tag}')
            st.dataframe(
                sub.groupby(['TEAM','項目'], as_index=False)['回数'].sum()
                   .sort_values(['TEAM','項目']),
                use_container_width=True
            )

            st.subheader(f'🎓 CLASS × TEAM × 項目 {scope_tag}')
            st.dataframe(
                sub.groupby(['CLASS','TEAM','項目'], as_index=False)['回数'].sum()
                   .sort_values(['CLASS','TEAM','項目']),
                use_container_width=True
            )

            st.subheader(f'⏱️ クォーター別：TEAM × 項目 {scope_tag}')
            st.dataframe(
                sub.groupby(['クォーター','TEAM','項目'], as_index=False)['回数'].sum()
                   .sort_values(['クォーター','TEAM','項目']),
                use_container_width=True
            )

            st.subheader(f'⏱️🎓 CLASS × クォーター × TEAM × 項目 {scope_tag}')
            st.dataframe(
                sub.groupby(['CLASS','クォーター','TEAM','項目'], as_index=False)['回数'].sum()
                   .sort_values(['CLASS','クォーター','TEAM','項目']),
                use_container_width=True
            )

            st.subheader(f'📌 選手 × 項目 {scope_tag}')
            st.dataframe(
                sub.groupby(['CLASS','TEAM','ビブスType','背番号','名前','項目'], as_index=False)['回数'].sum()
                   .sort_values(['CLASS','TEAM','背番号','名前','項目']),
                use_container_width=True
            )

            st.subheader(f'🙋‍♀️ 選手 × 項目（CLASSを選択）{scope_tag}')
            class_opts = sorted(sub['CLASS'].dropna().unique().tolist())
            sel_cls_foul = st.selectbox('CLASS を選択', class_opts, key='foul_cls_pick_for_players')
            cls_foul = sub[sub['CLASS'] == sel_cls_foul]
            if cls_foul.empty:
                st.info(f'{sel_cls_foul} のデータがありません。')
            else:
                st.dataframe(
                    cls_foul.groupby(['TEAM','ビブスType','背番号','名前','項目'], as_index=False)['回数'].sum()
                            .sort_values(['TEAM','背番号','名前','項目']),
                    use_container_width=True
                )

# これに置き換え（変数名を明示的に）
col_left, col_mid, col_right = st.columns([1, 2, 1])
with col_left:
    st.markdown("""
    <style>
      .btn-back {
        display:block; width:100%;
        text-align:center;
        padding:14px 16px; border-radius:14px;
        font-weight:700; font-size:18px;
        background:#efefef; border:1px solid #ddd;
        text-decoration:none !important; color:inherit;
      }
      .btn-back:active { transform: translateY(1px); }
    </style>
    <a class="btn-back" href="/" target="_self">⬅️ スコア画面へ戻る</a>
    """, unsafe_allow_html=True)
