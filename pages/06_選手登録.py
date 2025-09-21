import streamlit as st
import pandas as pd
import sqlite3

from app_auth import require_login, render_userbox

# 認証
require_login()
render_userbox(key="logout_button_register")  # ページ固有のキー

DB_PATH = 'players.db'

# --- DB初期化関数 ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uniform_number TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                bibs_type TEXT NOT NULL,
                class_type TEXT NOT NULL,
                UNIQUE(uniform_number, player_name, team, bibs_type, class_type)
            );
        ''')

init_db()

# --- CSSスタイル ---
st.markdown("""
<style>
  html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f4f7fa;
  }
</style>
""", unsafe_allow_html=True)

st.title("🏀選手登録")
st.caption("選手の背番号・名前・チーム・ビブスType・CLASSを登録・管理します")

# --- 入力フォーム ---
with st.form(key='player_register_form'):
    col1, col2 = st.columns(2)
    with col1:
        uniform_number = st.text_input("背番号", max_chars=4)
        player_name = st.text_input("プレイヤー名")
    with col2:
        team = st.selectbox("チーム", ("Red", "Blue"))
        bibs_type = st.selectbox("ビブスType", ("ドバスOriginal", "SPALDING", "無地"))

    class_type = st.radio("CLASS", ("初級", "中級", "上級"), horizontal=True)
    submit = st.form_submit_button("✅ 選手を登録", key="register_button")

# --- データベース操作関数 ---
def save_player(uniform_number, player_name, team, bibs_type, class_type):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO players
                (uniform_number, player_name, team, bibs_type, class_type)
                VALUES (?, ?, ?, ?, ?);
            ''', (uniform_number, player_name, team, bibs_type, class_type))
    except Exception as e:
        st.error(f"❌ 登録中にエラーが発生しました: {e}")

def delete_player(player_id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
            conn.commit()
    except Exception as e:
        st.error(f"❌ 削除中にエラーが発生しました: {e}")

def fetch_players():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM players", conn)

def safe_rerun():
    try:
        st.rerun()
    except:
        st.warning("🔄 手動でページを再読み込みしてください")

# --- 登録処理 ---
if submit:
    if uniform_number and player_name:
        save_player(uniform_number, player_name, team, bibs_type, class_type)
        st.success(f"🎉 選手 {player_name}（背番号: {uniform_number}）を登録しました！")
        safe_rerun()
    else:
        st.warning("⚠️ 背番号とプレイヤー名は必須です")

# --- 一覧表示＆削除 ---
st.subheader("📋 登録済み選手一覧")

df = fetch_players()
if not df.empty:
    df_show = df.drop(columns=['id'])
    st.dataframe(df_show, width='stretch')

    st.markdown("### ❌ 選手の削除")
    player_options = {
        f"{row['uniform_number']} - {row['player_name']} - {row['team']} - {row['bibs_type']} - {row['class_type']}": row['id']
        for _, row in df.iterrows()
    }
    selected_id = st.selectbox(
        "削除する選手を選択",
        options=list(player_options.values()),
        format_func=lambda x: [k for k, v in player_options.items() if v == x][0],
        key="delete_select"
    )

    confirm = st.checkbox("⚠️ 本当にこの選手を削除しますか？", key="confirm_delete")
    if st.button("❌ この選手を削除", key="delete_button") and confirm:
        delete_player(selected_id)
        st.success("✅ 選手を削除しました！")
        safe_rerun()
else:
    st.info("まだ選手は登録されていません。")
