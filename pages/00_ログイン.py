# pages/00_ログイン.py
import streamlit as st
from lib_db import get_conn, inject_css, inject_mobile_big_ui
from app_auth import ensure_users_table, users_count, create_user, authenticate

# set_page_config は最初の1回だけ
if not st.session_state.get("_pc_set", False):
    try:
        st.set_page_config(
            page_title="ログイン",
            page_icon="🔐",
            layout="centered",
            initial_sidebar_state="expanded",
        )
    except Exception:
        pass
    st.session_state["_pc_set"] = True

inject_css()
inject_mobile_big_ui()

# ログイン画面用CSS
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%);
    }

    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }

    .login-hero {
        text-align: center;
        padding: 28px 20px 10px;
    }

    .login-icon {
        font-size: 56px;
        margin-bottom: 8px;
    }

    .login-title {
        font-size: 34px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 6px;
    }

    .login-subtitle {
        color: #64748b;
        font-size: 15px;
        margin-bottom: 24px;
    }

    .login-card {
        background: rgba(255, 255, 255, 0.92);
        padding: 28px 28px 24px;
        border-radius: 24px;
        box-shadow: 0 20px 50px rgba(15, 23, 42, 0.12);
        border: 1px solid rgba(148, 163, 184, 0.25);
        backdrop-filter: blur(10px);
    }

    .login-card-title {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 6px;
    }

    .login-card-desc {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 18px;
    }

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] button {
        width: 100%;
        border-radius: 999px;
        height: 46px;
        font-weight: 700;
        border: none;
        background: linear-gradient(135deg, #2563eb, #06b6d4);
        color: white;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
        transition: 0.2s ease;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 28px rgba(37, 99, 235, 0.32);
        color: white;
    }

    input {
        border-radius: 12px !important;
    }

    .footer-text {
        text-align: center;
        color: #94a3b8;
        font-size: 12px;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

conn = get_conn()
ensure_users_table(conn)

st.markdown(
    """
    <div class="login-hero">
        <div class="login-icon">🏀</div>
        <div class="login-title">Score Sheet App</div>
        <div class="login-subtitle">スコア管理システムへようこそ</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="login-card">', unsafe_allow_html=True)

if users_count(conn) == 0:
    st.markdown(
        """
        <div class="login-card-title">初回セットアップ</div>
        <div class="login-card-desc">最初の管理者ユーザーを作成してください。</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("admin_create"):
        admin_user = st.text_input("ユーザー名", placeholder="例: admin")
        pw1 = st.text_input("パスワード", type="password")
        pw2 = st.text_input("パスワード（確認）", type="password")
        ok = st.form_submit_button("👑 管理者を作成")

    if ok:
        if not admin_user or not pw1:
            st.error("ユーザー名/パスワードは必須です。")
        elif pw1 != pw2:
            st.error("確認用パスワードが一致しません。")
        else:
            ok, msg = create_user(conn, admin_user, pw1, role="admin")
            if ok:
                st.success(msg + " ログインしてください。")
            else:
                st.error(msg)

else:
    st.markdown(
        """
        <div class="login-card-title">ログイン</div>
        <div class="login-card-desc">ユーザー名とパスワードを入力してください。</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login"):
        username = st.text_input("ユーザー名", placeholder="ユーザー名を入力")
        password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
        ok = st.form_submit_button("➡️ ログイン")

    if ok:
        user = authenticate(conn, username, password)
        if user:
            st.session_state["auth_user"] = user
            st.success("ログインしました。")

            try:
                if hasattr(st, "switch_page"):
                    st.switch_page("main.py")
            except Exception:
                pass

            st.markdown('<a href="/" target="_self">🏠 メインへ移動</a>', unsafe_allow_html=True)
            st.stop()
        else:
            st.error("ユーザー名またはパスワードが違います。")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="footer-text">
        © Score Sheet App
    </div>
    """,
    unsafe_allow_html=True,
)