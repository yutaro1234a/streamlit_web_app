import streamlit as st
import pandas as pd
import sqlite3

from app_auth import require_login, render_userbox

require_login()
try:
    render_userbox(key="logout_button_register")
except TypeError:
    render_userbox()

DB_PATH = "players.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uniform_number TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                bibs_type TEXT NOT NULL,
                class_type TEXT NOT NULL,
                UNIQUE(uniform_number, player_name, team, bibs_type, class_type)
            );
        """)

init_db()

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 45%, #e0f2fe 100%);
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

.page-hero {
    padding: 20px 6px 10px;
    text-align: center;
}

.page-title {
    font-size: 36px;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 6px;
}

.page-subtitle {
    color: #64748b;
    font-size: 15px;
}

.card {
    background: rgba(255, 255, 255, 0.94);
    padding: 26px 28px;
    border-radius: 24px;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.10);
    border: 1px solid rgba(148, 163, 184, 0.25);
    margin: 18px 0;
}

.card-title {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 4px;
}

.card-desc {
    color: #64748b;
    font-size: 14px;
    margin-bottom: 18px;
}

div[data-testid="stFormSubmitButton"] button,
div.stButton > button {
    width: 100%;
    border-radius: 999px;
    height: 46px;
    font-weight: 800;
    border: none;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: white;
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
}

div[data-testid="stFormSubmitButton"] button:hover,
div.stButton > button:hover {
    transform: translateY(-1px);
    color: white;
    box-shadow: 0 14px 28px rgba(37, 99, 235, 0.32);
}

input, textarea {
    border-radius: 12px !important;
}

[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
}

.warning-box {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    color: #9a3412;
    padding: 14px 16px;
    border-radius: 16px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-hero">
    <div class="page-title">🏀 選手登録</div>
    <div class="page-subtitle">背番号・名前・チーム・ビブスType・CLASSを登録・管理します</div>
</div>
""", unsafe_allow_html=True)

def save_player(uniform_number, player_name, team, bibs_type, class_type):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO players
                (uniform_number, player_name, team, bibs_type, class_type)
                VALUES (?, ?, ?, ?, ?);
            """, (uniform_number, player_name, team, bibs_type, class_type))
            conn.commit()
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
    except Exception:
        st.warning("🔄 手動でページを再読み込みしてください")

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("""
<div class="card-title">📝 新規選手登録</div>
<div class="card-desc">登録したい選手情報を入力してください。</div>
""", unsafe_allow_html=True)

with st.form(key="player_register_form"):
    col1, col2 = st.columns(2)

    with col1:
        uniform_number = st.text_input("背番号", max_chars=4, placeholder="例: 11")
        player_name = st.text_input("プレイヤー名", placeholder="例: 山田 太郎")

    with col2:
        team = st.selectbox("チーム", ("Red", "Blue"))
        bibs_type = st.selectbox("ビブスType", ("ドバスOriginal", "SPALDING", "無地"))

    class_type = st.radio("CLASS", ("初級", "中級", "上級"), horizontal=True)
    submit = st.form_submit_button("✅ 選手を登録")

st.markdown("</div>", unsafe_allow_html=True)

if submit:
    if uniform_number and player_name:
        save_player(uniform_number, player_name, team, bibs_type, class_type)
        st.success(f"🎉 選手 {player_name}（背番号: {uniform_number}）を登録しました！")
        safe_rerun()
    else:
        st.warning("⚠️ 背番号とプレイヤー名は必須です")

df = fetch_players()

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("""
<div class="card-title">📋 登録済み選手一覧</div>
<div class="card-desc">現在登録されている選手を確認できます。</div>
""", unsafe_allow_html=True)

if not df.empty:
    df_show = df.drop(columns=["id"])
    st.dataframe(df_show, width="stretch")

    st.markdown("---")
    st.markdown("### 🗑️ 選手の削除")

    player_options = {
        f"{row['uniform_number']} - {row['player_name']} - {row['team']} - {row['bibs_type']} - {row['class_type']}": row["id"]
        for _, row in df.iterrows()
    }

    selected_id = st.selectbox(
        "削除する選手を選択",
        options=list(player_options.values()),
        format_func=lambda x: [k for k, v in player_options.items() if v == x][0],
        key="delete_select",
    )

    confirm = st.checkbox("⚠️ 本当にこの選手を削除しますか？", key="confirm_delete")

    if st.button("❌ この選手を削除", key="delete_button") and confirm:
        delete_player(selected_id)
        st.success("✅ 選手を削除しました！")
        safe_rerun()

else:
    st.info("まだ選手は登録されていません。")

st.markdown("</div>", unsafe_allow_html=True)