import streamlit as st
from lib_db import get_conn, inject_css, inject_mobile_big_ui
from app_auth import ensure_users_table, users_count, create_user, authenticate

# =========================
# ページ設定
# =========================
if not st.session_state.get("_pc_set", False):
    st.set_page_config(
        page_title="Login",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.session_state["_pc_set"] = True

# =========================
# ★ここが重要（毎回実行）
# =========================
st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

inject_css()
inject_mobile_big_ui()

# =========================
# シンプルモダンCSS
# =========================
st.markdown("""
<style>

/* 背景 */
html, body, .stApp {
    background: #f8fafc;
}

/* 中央配置 */
.block-container {
    max-width: 420px;
    margin: auto;
    padding-top: 80px;
}

/* ロゴ */
.logo {
    display: flex;
    justify-content: center;
    margin-bottom: 10px;
}

/* SVG軽アニメ */
.logo svg {
    width: 64px;
    height: 64px;
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
    100% { transform: translateY(0px); }
}

/* タイトル */
.title {
    text-align: center;
    font-size: 26px;
    font-weight: 800;
    color: #0f172a;
}

.subtitle {
    text-align: center;
    color: #64748b;
    font-size: 13px;
    margin-bottom: 25px;
}

/* カード */
.card {
    background: white;
    padding: 26px;
    border-radius: 18px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.05);
}

/* ボタン */
div.stButton > button,
div[data-testid="stFormSubmitButton"] button {
    width: 100%;
    height: 44px;
    border-radius: 999px;
    font-weight: 700;
    border: none;
    background: #2563eb;
    color: white;
}

div.stButton > button:hover,
div[data-testid="stFormSubmitButton"] button:hover {
    background: #1d4ed8;
}

/* 入力 */
input {
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# DB
# =========================
conn = get_conn()
ensure_users_table(conn)

# =========================
# ヘッダー
# =========================
st.markdown("""
<div class="logo">
<svg viewBox="0 0 24 24" fill="none">
<circle cx="12" cy="12" r="10" stroke="#2563eb" stroke-width="2"/>
<path d="M2 12h20M12 2c3 3 3 17 0 20" stroke="#2563eb" stroke-width="2"/>
</svg>
</div>

<div class="title">Score Sheet</div>
<div class="subtitle">ログインして続行してください</div>
""", unsafe_allow_html=True)

# =========================
# カード
# =========================
st.markdown('<div class="card">', unsafe_allow_html=True)

# 初回
if users_count(conn) == 0:

    st.markdown("### 初回セットアップ")

    with st.form("admin_create"):
        admin_user = st.text_input("ユーザー名")
        pw1 = st.text_input("パスワード", type="password")
        pw2 = st.text_input("確認用パスワード", type="password")
        ok = st.form_submit_button("管理者を作成")

    if ok:
        if not admin_user or not pw1:
            st.error("必須項目です")
        elif pw1 != pw2:
            st.error("パスワード不一致")
        else:
            ok, msg = create_user(conn, admin_user, pw1, role="admin")
            if ok:
                st.success("作成完了！ログインしてください")
            else:
                st.error(msg)

# ログイン
else:

    with st.form("login"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        ok = st.form_submit_button("ログイン")

    if ok:
        user = authenticate(conn, username, password)
        if user:
            st.session_state["auth_user"] = user
            st.success("ログイン成功")

            try:
                st.switch_page("main.py")
            except Exception:
                pass
        else:
            st.error("認証失敗")

st.markdown("</div>", unsafe_allow_html=True)