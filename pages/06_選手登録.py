import streamlit as st
import pandas as pd
import sqlite3
import os

from app_auth import require_login, render_userbox

require_login()
render_userbox()

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

# --- CSSスタイリング ---
st.markdown("""
<style>
  html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f4f7fa;
  }
  .circle-button {
    display: inline-block;
    border-radius: 50%;
    width: 100px;
    height: 100px;
    line-height: 100px;
    text-align: center;
    font-weight: bold;
    background: linear-gradient(45deg, #ffcc00, #ff0066);
    color: white;
    box-shadow: 0 5px 0 #e6d900;
    transition: all 0.2s ease;
  }
  .circle-button:hover {
    transform: translate(0, 3px);
    box-shadow: 0 2px 0 #e6d900;
  }
  .confirm-box {
    padding: 1rem;
    border: 2px dashed #f36;
    background-color: #fff0f5;
    border-radius: 10px;
    margin-bottom: 1rem;
  }
  .confirm-box p {
    font-weight: bold;
    color: #d33;
  }
</style>
""", unsafe_allow_html=True)

st.title("\U0001F3C0選手登録")
st.caption("選手の背番号・名前・チーム・ビブスType・CLASSを登録します")

# 入力フォーム
with st.form(key='player_register_form'):
    col1, col2 = st.columns(2)
    with col1:
        uniform_number = st.text_input("背番号", max_chars=4)
        player_name = st.text_input("プレイヤー名")
    with col2:
        team = st.selectbox("チーム", ("Red", "Blue"))
        bibs_type = st.selectbox("ビブスType", ("ドバスOriginal", "SPALDING", "無地"))

    class_type = st.radio("CLASS", ("初級", "中級", "上級"), horizontal=True)
    submit = st.form_submit_button("✅ 選手を登録")

# DB登録処理
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

if submit:
    if uniform_number and player_name:
        save_player(uniform_number, player_name, team, bibs_type, class_type)
        st.success(f"🎉 選手 {player_name}（背番号: {uniform_number}）を登録しました！")
        st.rerun()
    else:
        st.warning("⚠️ 背番号とプレイヤー名は必須です")

# 登録済み選手の表示と削除
def fetch_players():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM players", conn)

def delete_player(player_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM players WHERE id = ?", (player_id,))

st.write("\n")
st.subheader("\U0001F4CB 登録済み選手一覧")

df = fetch_players()
if not df.empty:
    st.dataframe(df.drop(columns=['id']))

    st.write("\n")
    st.markdown("### ❌ 選手の削除")
    df['label'] = df.apply(lambda row: f"{row['uniform_number']} - {row['player_name']} - {row['team']} - {row['bibs_type']} - {row['class_type']}", axis=1)
    selected_label = st.selectbox("削除する選手を選択", df['label'].tolist())
    selected_id = df[df['label'] == selected_label]['id'].values[0]

    confirm_delete = st.checkbox("⚠️ 本当にこの選手を削除しますか？")
    if st.button("❌ この選手を削除") and confirm_delete:
        delete_player(selected_id)
        st.success("✅ 選手を削除しました！")
        st.rerun()
else:
    st.info("まだ選手は登録されていません")
