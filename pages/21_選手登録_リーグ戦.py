import streamlit as st
import sqlite3
import pandas as pd

# ✅ ログイン必須
from app_auth import render_userbox

st.set_page_config(layout="wide")  # スマホ最適化

if "auth_user" not in st.session_state:
    st.switch_page("pages/00_ログイン.py")
    st.stop()

try:
    render_userbox(key="logout_button_league_register")
except TypeError:
    render_userbox()

# --- DBパス ---
DB_PATH = "league.db"

# --- DB初期化 ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS league_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                uniform_number TEXT NOT NULL,
                player_name TEXT NOT NULL,
                UNIQUE(team, uniform_number)
            );
        ''')

# --- DB操作 ---
def save_player(team, number, name):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute(
                "INSERT INTO league_players (team, uniform_number, player_name) VALUES (?, ?, ?);",
                (team, number, name)
            )
        except sqlite3.IntegrityError:
            st.warning("⚠️ 同じチームに同じ背番号の選手がすでに登録されています")

def delete_player(player_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM league_players WHERE id=?", (player_id,))

def fetch_players(team=None):
    with sqlite3.connect(DB_PATH) as conn:
        if team:
            return pd.read_sql_query("SELECT * FROM league_players WHERE team=? ORDER BY uniform_number;", conn, params=(team,))
        return pd.read_sql_query("SELECT * FROM league_players ORDER BY team, uniform_number;", conn)

# 初期化
init_db()

# --- UI ---
st.title("🏀 リーグ戦：選手登録フォーム")
st.caption("チームごとに選手を登録・管理します")

# チーム選択
team = st.selectbox("🧩 チームを選択", ["A", "B", "C", "D"])

# 入力フォーム
st.markdown("### ➕ 新しい選手を追加")
with st.form(key="player_form"):
    col1, col2 = st.columns(2)
    with col1:
        number = st.text_input("🎽 背番号", max_chars=4)
    with col2:
        name = st.text_input("🏷️ 選手名")

    submitted = st.form_submit_button("✅ 登録")
    if submitted:
        if number and name:
            save_player(team, number, name)
            st.success(f"✅ {team}チームに選手 {name}（背番号:{number}）を登録しました")
            st.session_state["rerun_needed"] = True
        else:
            st.warning("⚠️ 背番号と選手名は必須です")

# 選手一覧
st.markdown("### 📋 登録済み選手一覧")
df = fetch_players(team)

if df.empty:
    st.info("このチームにはまだ選手が登録されていません。")
else:
    for _, row in df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([4, 4, 2])
            with col1:
                st.markdown(f"<span style='font-size:20px;'>🎽 <strong>背番号:</strong> {row['uniform_number']}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<span style='font-size:20px;'>🏷️ <strong>名前:</strong> {row['player_name']}</span>", unsafe_allow_html=True)
            with col3:
                if st.button("🗑️ 削除", key=f"del_{row['id']}"):
                    delete_player(row['id'])
                    st.success("🗑️ 選手を削除しました")
                    st.session_state["rerun_needed"] = True

# 🔄 必要に応じてリロード
if st.session_state.get("rerun_needed"):
    st.session_state.pop("rerun_needed")
    st.rerun()