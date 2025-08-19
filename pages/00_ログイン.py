# pages/00_ログイン.py
import streamlit as st
from lib_db import get_conn, inject_css, inject_mobile_big_ui
from auth import ensure_users_table, users_count, create_user, authenticate

# set_page_config は最初の1回だけ
if not st.session_state.get("_pc_set", False):
    try:
        st.set_page_config(page_title="🔐 ログイン", layout="centered", initial_sidebar_state="expanded")
    except Exception:
        pass
    st.session_state["_pc_set"] = True

inject_css()
inject_mobile_big_ui()

st.title("🔐 ログイン")
conn = get_conn()
ensure_users_table(conn)

if users_count(conn) == 0:
    st.info("初回セットアップ：管理者ユーザーを作成してください。")
    with st.form("admin_create"):
        admin_user = st.text_input("ユーザー名（例: admin）")
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
    st.caption("ユーザー名とパスワードを入力してください。")
    with st.form("login"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        ok = st.form_submit_button("➡️ ログイン")
    if ok:
        user = authenticate(conn, username, password)
        if user:
            st.session_state["auth_user"] = user
            st.success("ログインしました。")

            # メインへ遷移（できるだけ自動）
            try:
                if hasattr(st, "switch_page"):
                    st.switch_page("main.py")
            except Exception:
                pass
            st.markdown('<a href="/" target="_self">🏠 メインへ移動</a>', unsafe_allow_html=True)
            st.stop()
        else:
            st.error("ユーザー名またはパスワードが違います。")
