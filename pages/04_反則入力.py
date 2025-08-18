# pages/04_反則入力.py
import streamlit as st

# このページで最初の Streamlit コマンド
st.set_page_config(
    page_title="🚨 反則入力",
    layout="centered",
    initial_sidebar_state="expanded",
)

import time
import pandas as pd

from lib_db import (
    get_conn, inject_css, inject_mobile_big_ui, load_players, notify,
    add_event_sql, get_score_red_blue, read_recent_df, FOUL_SET
)

# set_page_config の後にスタイル適用
inject_css()
inject_mobile_big_ui()

# 必要なら使える安全リロード
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
st.session_state.setdefault("foul_last_action_ts", 0)

# タイトル & 固定バー
st.title("🚨 反則入力")
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

# 入力UI（キーはこのページ専用に）
classType = st.radio("🏫 CLASS", ("初級", "中級", "上級"), horizontal=True, key="foul_class_radio")
team      = st.radio("🟥 TEAM",  ("Red", "Blue"), horizontal=True, key="foul_team_radio")
quarter   = st.selectbox("⏱️ クォーター", ("Q1", "Q2", "Q3", "Q4", "OT"), key="foul_quarter_select")

# プレイヤー選択
filtered = players_df[(players_df["CLASS"] == classType) & (players_df["TEAM"] == team)].copy()
if not filtered.empty:
    display_options = filtered["表示"].tolist()
    selected_player = st.selectbox("🙋‍♂️ 選手（背番号 - 名前 - ビブス）", display_options, key="foul_player_select")
    row = filtered[filtered["表示"] == selected_player].iloc[0]
    uniformNumber = row["背番号"]; playerName = row["プレイヤー名"]; bibsType = row["ビブスType"]
else:
    st.warning(f"CLASS={classType} / TEAM={team} の選手がいません。先に選手登録をご確認ください。")
    uniformNumber = "--"; playerName = ""; bibsType = ""

# 登録関数（誤連打ガード / 反則のみ受け付け）
def add_foul(action_label: str):
    now = time.time()
    if now - st.session_state.foul_last_action_ts < 0.35:
        return
    if uniformNumber == "--":
        st.error("選手が未選択です。")
        return
    if action_label not in FOUL_SET:
        st.error("反則以外の項目は登録できません。")
        return
    _ = add_event_sql(conn, classType, team, bibsType, uniformNumber, playerName, action_label, quarter)
    st.session_state.foul_last_action_ts = now
    notify(f"登録: {playerName} / {action_label} / {quarter}", icon="✅")

# 反則ボタン
st.caption("タップで即登録（ファール / ターンオーバー）")
c1, c2 = st.columns(2)
with c1:
    st.button("🚨 ファール", on_click=add_foul, args=("ファール",), use_container_width=True)
with c2:
    st.button("♻️ ターンオーバー", on_click=add_foul, args=("ターンオーバー",), use_container_width=True)

# 直近反則ログ（プルダウンで開く）
st.markdown("---")
with st.expander("📋 直近反則ログ（タップで開く）", expanded=False):
    N = st.number_input("表示件数（取得後に反則で絞り込み）", min_value=5, max_value=300, value=30, step=5, key="foul_recent_n")
    recent = read_recent_df(conn, n=int(N))
    # 反則のみ抽出
    if not recent.empty and "得点・アシスト" in recent.columns:
        recent = recent[recent["得点・アシスト"].isin(FOUL_SET)]
    if recent.empty:
        st.info("表示できる反則データがありません。")
    else:
        order = ['id','created_at','CLASS','TEAM','ビブスType','背番号','名前','得点・アシスト','クォーター']
        cols = [c for c in order if c in recent.columns] + [c for c in recent.columns if c not in order]
        st.dataframe(recent[cols], use_container_width=True, height=360)

# ナビゲーション（同一タブ）
st.markdown("---")
if hasattr(st, "page_link"):
    cols_nav = st.columns(3)
    with cols_nav[0]:
        st.page_link("main.py", label="🏠 メイン（入力＆ログ）", icon="🏠", use_container_width=True)
    with cols_nav[1]:
        st.page_link("pages/01_集計.py", label="📊 集計", icon="📊", use_container_width=True)
    with cols_nav[2]:
        # ほかの入力ページへの導線
        st.page_link("pages/02_得点入力.py", label="🏀 得点入力", icon="🏀", use_container_width=True)
        # 画面幅が狭いと縦に並ぶ場合がありますがそのままでOK
