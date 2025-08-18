# pages/02_得点入力.py
import streamlit as st
from ui_components import inject_touch_ui_css, inject_compact_pick_css, radio_compact

# このページの最初の Streamlit コマンド
st.set_page_config(
    page_title="🏀SCORE INPUT",
    layout="centered",
    initial_sidebar_state="expanded",
)

import time
import pandas as pd

from lib_db import (
    get_conn, inject_css, inject_mobile_big_ui, load_players, notify,
    add_event_sql, get_score_red_blue, read_recent_df
)

# set_page_config の後に呼ぶ（内部で st.markdown を使うため）
inject_css()
inject_mobile_big_ui()
inject_touch_ui_css()
inject_compact_pick_css()

# どのバージョンでも動くリロード（必要時）
def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            try:
                st.toast("🔄 画面を更新してください（ブラウザの再読み込み）", icon="🔄")
            except Exception:
                st.warning("🔄 画面を更新してください（Ctrl/Cmd + R）")

# DB / データ
conn = get_conn()
players_df = load_players()

# 状態
st.session_state.setdefault("last_action_ts", 0)

# タイトル & 固定バー
st.title("🏀SCORE")
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

# 入力UI（キーはこのページ専用に）
# CLASS / TEAM / QUARTER を “ピル型セグメント” に
row1_left, row1_right = st.columns(2)
with row1_left:
    class_opts = ["初級", "中級", "上級"]
    classType = radio_compact("🚀 CLASS", class_opts, key="score_class_radio_compact",
                              index=class_opts.index(st.session_state.get("score_class_radio_compact",
                                                                          st.session_state.get("score_class_radio", "初級")))
                             )
with row1_right:
    # 直感性UPのため絵文字で色を表現
    team_opts_lbl = ["🔴 Red", "🔵 Blue"]
    team_lbl = radio_compact("🟥 TEAM", team_opts_lbl, key="score_team_radio_compact",
                             index=0 if st.session_state.get("score_team_radio", "Red") == "Red" else 1)
    team = "Red" if "Red" in team_lbl else "Blue"

# 2段目：QUARTER（左：小さめピル） / 選手（右：セレクト）
row2_left, row2_right = st.columns([1, 2])  # 選手に多く幅を割り当て
with row2_left:
    q_opts = ["Q1", "Q2", "Q3", "Q4", "OT"]
    quarter = radio_compact("⏱️ Quarter", q_opts, key="score_quarter_radio_compact",
                             index=q_opts.index(st.session_state.get("score_quarter_radio_compact",
                                                                     st.session_state.get("score_quarter_select", "Q1")))
                            )
with row2_right:
    # プレイヤー選択（検索可）も省スペース化：ラベル小さめ・上下余白圧縮はCSSで済
    filtered = players_df[(players_df["CLASS"] == classType) & (players_df["TEAM"] == team)].copy()
    if not filtered.empty:
        display_options = filtered["表示"].tolist()
        selected_player = st.selectbox(
            "⛹️‍♂️ 選手（背番号 - 名前 - ビブス）",
            display_options,
            key="score_player_select"  # 従来キーのままでもOK
        )
        row = filtered[filtered["表示"] == selected_player].iloc[0]
        uniformNumber = row["背番号"]; playerName = row["プレイヤー名"]; bibsType = row["ビブスType"]
    else:
        st.warning(f"CLASS={classType} / TEAM={team} の選手がいません。先に選手登録をご確認ください。")
        uniformNumber = "--"; playerName = ""; bibsType = ""

# 登録関数（誤連打ガード）
def add_score(action_label: str):
    now = time.time()
    if now - st.session_state.last_action_ts < 0.35:
        return
    if uniformNumber == "--":
        st.error("選手が未選択です。")
        return
    _ = add_event_sql(conn, classType, team, bibsType, uniformNumber, playerName, action_label, quarter)
    st.session_state.last_action_ts = now
    notify(f"登録: {playerName} / {action_label} / {quarter}", icon="✅")

# 得点ボタン
st.caption("タップで登録")
c1, c2, c3 = st.columns(3)
with c1:
    st.button("🏀 3pt", on_click=add_score, args=("3pt",), use_container_width=True)
with c2:
    st.button("🏀 2pt", on_click=add_score, args=("2pt",), use_container_width=True)
with c3:
    st.button("🏀 1pt", on_click=add_score, args=("1pt",), use_container_width=True)

# 直近ログ（プルダウンで開く）
st.markdown("---")
with st.expander("📋 直近ログ得点ログ（タップで開く）", expanded=False):
    N = st.number_input("表示件数", min_value=5, max_value=200, value=20, step=5, key="score_recent_n")
    recent = read_recent_df(conn, n=int(N))

    if recent.empty or "得点・アシスト" not in recent.columns:
        st.info("表示できるデータがありません。")
    else:
        # ✅ 得点アクションだけ抽出
        score_actions = {"1pt", "2pt", "3pt"}
        recent_score = recent[recent["得点・アシスト"].isin(score_actions)].copy()

        if recent_score.empty:
            st.info("得点のログがありません。")
        else:
            # 見やすい列順に整列（存在する列だけ適用）
            order = ['id','created_at','CLASS','TEAM','ビブスType','背番号','名前','得点・アシスト','クォーター']
            cols = [c for c in order if c in recent_score.columns] + [c for c in recent_score.columns if c not in order]
            st.dataframe(recent_score[cols], use_container_width=True, height=360)

# ナビゲーション（同一タブ）
st.markdown("---")
if hasattr(st, "page_link"):
    cols_nav = st.columns(2)
    with cols_nav[0]:
        st.page_link("pages/01_集計.py", label="📊 集計", icon="➡️", use_container_width=True)
    with cols_nav[1]:
        st.write("")