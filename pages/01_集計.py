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

st.set_page_config(page_title="📊SCORE TALLY", layout="centered", initial_sidebar_state="expanded")
inject_css()
conn = get_conn()
        
st.title("📊SCORE TALLY")

# ♻️ 再集計案内（ページ実行でDB読み直し＝再集計）
if "agg_refresh_key" in st.session_state:
    try:
        st.toast("♻️ 集計しました", icon="♻️")
    except Exception:
        st.success("集計しました")
    del st.session_state["agg_refresh_key"]

# ─────────────────────────────────────────
# ⬅️ スコア画面
# ─────────────────────────────────────────

# 固定バー（全体スコア）
red_pts, blue_pts = get_score_red_blue(conn)
st.markdown(f"""
<div class="scorebar">
  <div class="scorebox">
    <div class="info">📊TOTAL SCORE</div>
    <div>
      <span class="scorechip red">Red: {red_pts}</span>
      <span class="scorechip blue">Blue: {blue_pts}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

df = read_df_sql(conn)
if df.empty:
    st.info("集計対象データがありません。"); 
    
    # これに置き換え（変数名を明示的に）
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:  # 中央に置きたいなら col_mid に変えてOK
        st.markdown("""
        <style>
        /* 共通スタイル */
        .btn-back-pc, .btn-back-sp {
            display:none;            /* まず両方隠す → メディアクエリで出す */
            width:100%;
            text-align:center;
            text-decoration:none !important;
            border:1px solid #ddd;
            border-radius:14px;
            font-weight:700;
        }
        .btn-back-pc:active, .btn-back-sp:active { transform: translateY(1px); }

        /* === PC / タブレット（幅768px以上）で表示 === */
        @media (min-width: 768px) {
            .btn-back-pc {
            display:block;
            background:#efefef; color:inherit;
            padding:14px 16px; font-size:18px;
            }
        }

        /* === スマホ（幅767px以下）で表示 === */
        @media (max-width: 767px) {
            .btn-back-sp {
            display:block;
            background:#111827; color:#fff;
            padding:16px 18px; font-size:20px;
            }
        }
        </style>

        <!-- PC用 / SP用 を両方描画して、CSSで出し分け -->
        <a class="btn-back-pc" href="/" target="_self">⬅️ main画面へ戻る</a>
        <a class="btn-back-sp" href="/" target="_self">⬅️ mainへ戻る</a>
        """, unsafe_allow_html=True)


    st.stop()

# 前処理
score_df = df[df['得点・アシスト'].isin(POINT_MAP.keys())].copy()
if not score_df.empty:
    score_df['得点'] = score_df['得点・アシスト'].map(POINT_MAP)

stat_df = df[df['得点・アシスト'].isin(STAT_SET)].copy().rename(columns={'得点・アシスト':'項目'}).assign(回数=1)
foul_df = df[df['得点・アシスト'].isin(FOUL_SET)].copy().rename(columns={'得点・アシスト':'項目'}).assign(回数=1)

tab_score, tab_stat, tab_foul = st.tabs(["🧮 得点", "📈 スタッツ", "🚨 反則"])

with tab_score:
    st.subheader('📌TEAMごとの得点')
    st.dataframe(
        score_df.groupby('TEAM', as_index=False)['得点'].sum()
        if not score_df.empty else pd.DataFrame({'TEAM': [], '得点': []}),
        use_container_width=True
    )

    st.subheader('🚀CLASSごとの得点')
    st.dataframe(
        score_df.groupby(['CLASS','TEAM'], as_index=False)['得点'].sum()
        if not score_df.empty else pd.DataFrame({'CLASS': [], 'TEAM': [], '得点': []}),
        use_container_width=True
    )

    st.subheader('⏱️🚀CLASS × QUARTERごとの得点')
    pivot = pd.pivot_table(
        score_df, index=['CLASS','クォーター'], columns='TEAM',
        values='得点', aggfunc='sum', fill_value=0
    )
    if {'Red','Blue'}.issubset(set(pivot.columns)):
        pivot['合計'] = pivot['Red'] + pivot['Blue']
    st.dataframe(pivot.reset_index(), use_container_width=True)

    st.subheader('🏅得点ランキング')
    N = st.number_input("得点ランキング", min_value=1, max_value=500, value=10, step=1, key="topN_all")
    per_player_all = (
        score_df.groupby(['CLASS','TEAM','ビブスType','背番号','名前'], as_index=False)['得点']
        .sum()
        .sort_values(['得点','CLASS','TEAM','背番号'], ascending=[False, True, True, True])
        .head(int(N))
    )
    st.dataframe(per_player_all, use_container_width=True)

    st.subheader('🏅CLASS別：得点ランキング')
    sel_cls = st.selectbox('CLASS を選択', ('初級','中級','上級'), key='cls_pick_for_topN')
    N_cls = st.number_input("上記何位まで", min_value=1, max_value=500, value=10, step=1, key="topN_cls")
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
    st.subheader('📌TEAM')
    if not stat_df.empty:
        # TEAM ごとのスタッツ（項目別）
        st.dataframe(
            stat_df.groupby(['TEAM','項目'], as_index=False)['回数'].sum(),
            use_container_width=True
        )

        # CLASS × TEAM ごとのスタッツ（項目別）
        st.subheader('🚀CLASSごとのスタッツ')
        st.dataframe(
            stat_df.groupby(['CLASS','TEAM','項目'], as_index=False)['回数'].sum(),
            use_container_width=True
        )

        # 選手 × 項目（CLASS選択）
        st.subheader('⛹️‍♂️選手ごとのスタッツ')
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
    st.subheader('🚨反則の集計')

    if foul_df.empty:
        st.info('反則のデータがありません。')
    else:
        # ▼ 「全体」を廃止。以前の選択が残っていても安全に正規化
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
        else:  # "ターンオーバーのみ"
            sub = foul_df[foul_df["項目"] == "ターンオーバー"].copy()
            scope_tag = "（ターンオーバーのみ）"

        if sub.empty:
            st.info(f"選択中の範囲 {scope_tag} にデータがありません。")
        else:
            st.subheader(f'📌TEAM {scope_tag}')
            st.dataframe(
                sub.groupby(['TEAM','項目'], as_index=False)['回数'].sum()
                   .sort_values(['TEAM','項目']),
                use_container_width=True
            )

            st.subheader(f'🚀CLASSごとの反則 {scope_tag}')
            st.dataframe(
                sub.groupby(['CLASS','TEAM','項目'], as_index=False)['回数'].sum()
                   .sort_values(['CLASS','TEAM','項目']),
                use_container_width=True
            )

            st.subheader(f'🚀⏱️CLASS × クォーターごとの反則 {scope_tag}')
            st.dataframe(
                sub.groupby(['クォーター','TEAM','項目'], as_index=False)['回数'].sum()
                   .sort_values(['クォーター','TEAM','項目']),
                use_container_width=True
            )

            st.subheader(f'⛹️‍♀️選手ごとの反則（CLASSを選択）{scope_tag}')
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
with col_mid:  # 中央に置きたいなら col_mid に変えてOK
    st.markdown("""
    <style>
      /* 共通スタイル */
      .btn-back-pc, .btn-back-sp {
        display:none;            /* まず両方隠す → メディアクエリで出す */
        width:100%;
        text-align:center;
        text-decoration:none !important;
        border:1px solid #ddd;
        border-radius:14px;
        font-weight:700;
      }
      .btn-back-pc:active, .btn-back-sp:active { transform: translateY(1px); }

      /* === PC / タブレット（幅768px以上）で表示 === */
      @media (min-width: 768px) {
        .btn-back-pc {
          display:block;
          background:#efefef; color:inherit;
          padding:14px 16px; font-size:18px;
        }
      }

      /* === スマホ（幅767px以下）で表示 === */
      @media (max-width: 767px) {
        .btn-back-sp {
          display:block;
          background:#111827; color:#fff;
          padding:16px 18px; font-size:20px;
        }
      }
    </style>

    <!-- PC用 / SP用 を両方描画して、CSSで出し分け -->
    <a class="btn-back-pc" href="/" target="_self">⬅️ main画面へ戻る</a>
    <a class="btn-back-sp" href="/" target="_self">⬅️ mainへ戻る</a>
    """, unsafe_allow_html=True)

