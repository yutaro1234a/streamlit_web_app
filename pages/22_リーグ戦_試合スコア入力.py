import streamlit as st
import sqlite3
import pandas as pd

# ✅ ログイン必須
from app_auth import render_userbox

st.set_page_config(layout="wide")  # スマホ最適化レイアウト

if "auth_user" not in st.session_state:
    st.switch_page("pages/00_ログイン.py")
try:
    render_userbox(key="logout_button_league_score")
except TypeError:
    render_userbox()

DB_PATH = "league.db"

# --- DB保存 ---
def save_match(team_1, team_2, score_1, score_2):
    if team_1 == team_2:
        st.error("同じチーム同士では試合できません。")
        return None

    winner = team_1 if score_1 > score_2 else team_2 if score_2 > score_1 else "引き分け"
    point_diff = abs(score_1 - score_2)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            INSERT INTO league_matches (team_1, team_2, score_1, score_2, winner, point_diff)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (team_1, team_2, score_1, score_2, winner, point_diff))
        return cur.lastrowid

# --- 削除 ---
def delete_match(match_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM league_matches WHERE id = ?", (match_id,))

# --- 取得 ---
def get_matches():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM league_matches ORDER BY id DESC", conn)

# --- UI ---
st.title("🎮 試合スコア登録フォーム")
st.caption("各チームの対戦結果を登録・管理できます")

team_list = ["A", "B", "C", "D"]

with st.form("score_input_form"):
    st.markdown("### ✍️ 試合情報を入力")
    col1, col2 = st.columns(2)
    with col1:
        team_1 = st.selectbox("対戦相手①", team_list, key="team_1")
        score_1 = st.number_input("得点（①）", min_value=0, step=1, key="score_1")
    with col2:
        team_2 = st.selectbox("対戦相手②", team_list, key="team_2")
        score_2 = st.number_input("得点（②）", min_value=0, step=1, key="score_2")

    submitted = st.form_submit_button("✅ 試合結果を登録")
    if submitted:
        match_id = save_match(team_1, team_2, int(score_1), int(score_2))
        if match_id:
            st.success("✅ 試合結果を登録しました")
            st.rerun()

# --- 試合一覧 ---
st.markdown("## 📋 登録済み試合結果")
matches = get_matches()

if matches.empty:
    st.info("まだ試合結果が登録されていません。")
else:
    for _, row in matches.iterrows():
        with st.container():
            st.markdown("---")
            st.markdown(f"### ⚔️ {row['team_1']} {row['score_1']} - {row['score_2']} {row['team_2']}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"🏅 **勝者:** {row['winner']}")
            with col2:
                st.markdown(f"📊 **得失点差:** {row['point_diff']}")
            st.markdown("")
            if st.button("🗑️ 削除", key=f"del_match_{row['id']}"):
                delete_match(row['id'])
                st.success("✅ 試合を削除しました")
                st.rerun()