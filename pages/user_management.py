import os
import sys
import streamlit as st
import pandas as pd

# =========================
# ページ設定
# =========================
if not st.session_state.get("_pc_set", False):
    try:
        st.set_page_config(
            page_title="👑 ユーザー管理",
            page_icon="👑",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
    except Exception:
        pass
    st.session_state["_pc_set"] = True

# Streamlit標準メニューを非表示（ログアウト後の再描画でも効くように毎回実行）
st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# import path
# =========================
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib_db import get_conn, inject_css, inject_mobile_big_ui

try:
    import app_auth as app_auth
except Exception as e:
    st.error(f"auth モジュールの読み込みに失敗しました: {e}")
    st.stop()

inject_css()
inject_mobile_big_ui()

# =========================
# 認証
# =========================
app_auth.require_login()
try:
    app_auth.render_userbox(key="logout_button_user_management")
except TypeError:
    app_auth.render_userbox()

me = app_auth.get_current_user()
if not me or me.get("role") != "admin":
    st.error("このページは管理者のみ利用できます。")
    st.stop()

# =========================
# モダンUI CSS
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

html, body, .stApp {
    background:
        radial-gradient(circle at 8% 10%, rgba(37, 99, 235, .14), transparent 30%),
        radial-gradient(circle at 92% 8%, rgba(168, 85, 247, .13), transparent 32%),
        linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%) !important;
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

.block-container {
    max-width: 1220px;
    padding-top: 1.3rem;
    padding-bottom: 3rem;
}

.user-hero {
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    padding: 30px 32px;
    margin: 8px 0 18px 0;
    color: #fff;
    background:
        radial-gradient(circle at 16% 0%, rgba(255,255,255,.30), transparent 26%),
        radial-gradient(circle at 86% 22%, rgba(96,165,250,.35), transparent 25%),
        linear-gradient(135deg, #0f172a 0%, #1e3a8a 52%, #312e81 100%);
    box-shadow: 0 22px 60px rgba(15, 23, 42, .24);
    isolation: isolate;
    animation: pageFadeIn .35s ease-out;
}

.user-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px);
    background-size: 34px 34px;
    mask-image: linear-gradient(90deg, rgba(0,0,0,.72), transparent 78%);
    z-index: -1;
}

.user-hero::after {
    content: "👑";
    position: absolute;
    right: 30px;
    top: 18px;
    font-size: 82px;
    opacity: .15;
    transform: rotate(-10deg);
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.24);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .06em;
    margin-bottom: 13px;
    backdrop-filter: blur(10px);
}

.hero-title {
    font-size: clamp(28px, 4vw, 42px);
    font-weight: 950;
    line-height: 1.12;
    margin: 0;
}

.hero-subtitle {
    color: rgba(255,255,255,.78);
    font-size: 14px;
    margin-top: 10px;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
    margin: 0 0 18px 0;
}

.kpi-card {
    position: relative;
    overflow: hidden;
    border-radius: 24px;
    padding: 18px 20px;
    background: rgba(255,255,255,.86);
    border: 1px solid rgba(255,255,255,.94);
    box-shadow: 0 14px 34px rgba(15, 23, 42, .08);
    backdrop-filter: blur(14px);
}

.kpi-label {
    color: #64748b;
    font-size: 12px;
    font-weight: 950;
    letter-spacing: .08em;
}

.kpi-value {
    color: #0f172a;
    font-size: 32px;
    font-weight: 950;
    line-height: 1.05;
    margin-top: 8px;
    font-variant-numeric: tabular-nums;
}

.kpi-note {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 800;
    margin-top: 8px;
}

.section-card {
    border-radius: 24px;
    padding: 18px 20px;
    margin: 18px 0 12px 0;
    background: rgba(255,255,255,.84);
    border: 1px solid rgba(255,255,255,.92);
    box-shadow: 0 12px 30px rgba(15, 23, 42, .08);
    backdrop-filter: blur(14px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #0f172a;
    font-size: 18px;
    font-weight: 950;
}

.section-title span:first-child {
    width: 36px;
    height: 36px;
    border-radius: 14px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #eff6ff;
}

.section-caption {
    color: #64748b;
    font-size: 13px;
    margin-top: 4px;
    margin-left: 46px;
}

.section-card::after {
    content: "";
    width: 88px;
    height: 8px;
    border-radius: 999px;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    opacity: .72;
    flex: 0 0 auto;
}

.panel-card {
    border-radius: 24px;
    padding: 22px 22px;
    background: rgba(255,255,255,.86);
    border: 1px solid rgba(255,255,255,.94);
    box-shadow: 0 14px 34px rgba(15, 23, 42, .08);
    backdrop-filter: blur(14px);
    margin-bottom: 14px;
}

.panel-title {
    color: #0f172a;
    font-size: 17px;
    font-weight: 950;
    margin-bottom: 4px;
}

.panel-desc {
    color: #64748b;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 14px;
}

.danger-panel {
    border-color: rgba(252, 165, 165, .75);
    background: rgba(255, 247, 247, .92);
}

.selected-user {
    border-radius: 18px;
    padding: 13px 15px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    color: #334155;
    font-size: 13px;
    font-weight: 850;
    margin-bottom: 14px;
}

div[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(226,232,240,.92);
    box-shadow: 0 10px 24px rgba(15, 23, 42, .055);
}

div[data-testid="stDataFrame"] [role="columnheader"] {
    background: #f8fafc !important;
    color: #0f172a !important;
    font-weight: 900 !important;
}

div[data-baseweb="select"] > div,
input {
    border-radius: 14px !important;
    border-color: #dbe3ef !important;
    background-color: rgba(255,255,255,.92) !important;
}

.stTextInput label,
.stSelectbox label {
    font-weight: 900 !important;
    color: #334155 !important;
}

div.stButton > button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stPageLink"] a {
    border-radius: 999px !important;
    height: 44px;
    font-weight: 900 !important;
    border: 1px solid rgba(15, 23, 42, .10) !important;
    box-shadow: 0 10px 22px rgba(15, 23, 42, .08) !important;
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
    color: white !important;
}

div[data-testid="stFormSubmitButton"] button:hover,
div.stButton > button:hover,
div[data-testid="stPageLink"] a:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 30px rgba(37, 99, 235, .18) !important;
}

[data-testid="stExpander"] {
    border-radius: 18px !important;
    border: 1px solid #e2e8f0 !important;
    background: rgba(255,255,255,.78) !important;
    overflow: hidden;
}

@keyframes pageFadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 900px) {
    .kpi-grid {
        grid-template-columns: 1fr;
    }

    .section-card {
        align-items: flex-start;
    }

    .section-card::after {
        display: none;
    }

    .section-caption {
        margin-left: 0;
    }
}
</style>
""", unsafe_allow_html=True)


def section_header(icon, title, caption):
    st.markdown(
        f"""
        <div class="section-card">
            <div>
                <div class="section-title"><span>{icon}</span><span>{title}</span></div>
                <div class="section-caption">{caption}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


# =========================
# DB準備
# =========================
conn = get_conn()
app_auth.ensure_users_table(conn)

rows = app_auth.list_users(conn)
df = (
    pd.DataFrame(rows, columns=["id", "username", "role", "created_at"])
    if rows
    else pd.DataFrame(columns=["id", "username", "role", "created_at"])
)

admin_count = int((df["role"] == "admin").sum()) if not df.empty else 0
user_count = int((df["role"] == "user").sum()) if not df.empty else 0
total_count = int(len(df))

# =========================
# ヘッダー
# =========================
st.markdown(
    """
    <div class="user-hero">
        <div class="hero-badge">👑 USER ADMINISTRATION</div>
        <div class="hero-title">ユーザー管理</div>
        <div class="hero-subtitle">アカウント作成・権限変更・パスワードリセット・削除を管理します。</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">TOTAL USERS</div>
            <div class="kpi-value">{total_count}</div>
            <div class="kpi-note">登録ユーザー数</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">ADMINS</div>
            <div class="kpi-value">{admin_count}</div>
            <div class="kpi-note">管理者アカウント</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">GENERAL USERS</div>
            <div class="kpi-value">{user_count}</div>
            <div class="kpi-note">一般ユーザー</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# ユーザー一覧
# =========================
section_header("👥", "ユーザー一覧", "登録済みユーザーを確認し、条件で絞り込みできます。")

if df.empty:
    st.info("ユーザーがいません。まずは『ユーザー追加』から作成してください。")
else:
    with st.expander("🔎 フィルタ", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            q = st.text_input("ユーザー名で絞り込み（部分一致）", value="", key="user_filter_q")
        with c2:
            role_pick = st.selectbox("ロールで絞り込み", ("すべて", "admin", "user"), key="user_filter_role")

    view = df.copy()
    if q.strip():
        view = view[view["username"].astype(str).str.contains(q.strip(), na=False)]
    if role_pick != "すべて":
        view = view[view["role"] == role_pick]

    st.dataframe(view.sort_values(["id"]), width="stretch", height=300, hide_index=True)

# =========================
# 追加・編集
# =========================
col_add, col_edit = st.columns(2)

with col_add:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">➕ ユーザー追加</div>
            <div class="panel-desc">新しいログインユーザーを作成します。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("add_user"):
        new_u = st.text_input("ユーザー名", key="add_user_name", placeholder="例: user01")
        new_p1 = st.text_input("パスワード", type="password", key="add_user_pw1")
        new_p2 = st.text_input("パスワード（確認）", type="password", key="add_user_pw2")
        new_role = st.selectbox("ロール", ["user", "admin"], key="add_user_role")
        ok_add = st.form_submit_button("ユーザーを作成", width="stretch")

    if ok_add:
        if not new_u or not new_p1:
            st.error("ユーザー名／パスワードは必須です。")
        elif new_p1 != new_p2:
            st.error("確認用パスワードが一致しません。")
        else:
            ok, msg = app_auth.create_user(conn, new_u, new_p1, role=new_role)
            (st.success if ok else st.error)(msg)
            if ok:
                safe_rerun()

with col_edit:
    st.markdown(
        """
        <div class="panel-card">
            <div class="panel-title">🛠️ 既存ユーザー管理</div>
            <div class="panel-desc">ユーザー名・ロール・パスワード・削除を管理します。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("ユーザーがいません。")
    else:
        options = [f"{int(r.id)}: {r.username} ({r.role})" for _, r in df.sort_values("id").iterrows()]
        pick = st.selectbox("対象ユーザーを選択", options, key="edit_user_pick")
        sel_id = int(pick.split(":")[0]) if pick else None
        sel_row = df[df["id"] == sel_id].iloc[0] if sel_id in df["id"].values else None

        if sel_row is not None:
            st.markdown(
                f"""
                <div class="selected-user">
                    選択中：ID={int(sel_row.id)} / {sel_row.username} / role={sel_row.role}
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("edit_username"):
                new_name = st.text_input("新しいユーザー名", value=sel_row.username, key="edit_username_value")
                ok_uname = st.form_submit_button("✏️ ユーザー名を変更", width="stretch")
            if ok_uname:
                ok, msg = app_auth.change_username(conn, user_id=int(sel_row.id), new_username=new_name)
                (st.success if ok else st.error)(msg)
                if ok:
                    safe_rerun()

            with st.form("edit_role"):
                role_new = st.selectbox(
                    "ロールを変更",
                    ["user", "admin"],
                    index=0 if sel_row.role == "user" else 1,
                    key="edit_role_value",
                )
                ok_role = st.form_submit_button("🔁 ロールを変更", width="stretch")
            if ok_role:
                try:
                    conn.execute("UPDATE users SET role=? WHERE id=?", (role_new, int(sel_row.id)))
                    conn.commit()
                    st.success("ロールを変更しました。")
                    safe_rerun()
                except Exception as e:
                    st.error(f"ロール変更に失敗しました: {e}")

            with st.form("reset_pw"):
                pw1 = st.text_input("新しいパスワード", type="password", key="reset_pw1")
                pw2 = st.text_input("新しいパスワード（確認）", type="password", key="reset_pw2")
                ok_pw = st.form_submit_button("🔐 パスワードをリセット", width="stretch")
            if ok_pw:
                if pw1 != pw2:
                    st.error("確認用パスワードが一致しません。")
                elif not pw1:
                    st.error("新しいパスワードを入力してください。")
                else:
                    ok, msg = app_auth.admin_set_password(conn, int(sel_row.id), pw1)
                    (st.success if ok else st.error)(msg)

            st.markdown(
                """
                <div class="panel-card danger-panel">
                    <div class="panel-title">🗑️ ユーザー削除</div>
                    <div class="panel-desc">この操作は取り消せません。確認文字を入力してください。</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("delete_user"):
                confirm_txt = st.text_input(
                    f"確認用に「DELETE {int(sel_row.id)}」と入力してください",
                    key="delete_confirm_txt",
                )
                ok_del = st.form_submit_button("🗑️ ユーザーを削除", width="stretch")
            if ok_del:
                if confirm_txt.strip() == f"DELETE {int(sel_row.id)}":
                    ok, msg = app_auth.admin_delete_user(conn, int(sel_row.id), acting_user_id=int(me["id"]))
                    (st.success if ok else st.error)(msg)
                    if ok:
                        safe_rerun()
                else:
                    st.error("確認文字が一致しません。")

# =========================
# 戻る
# =========================
st.divider()

cols_top = st.columns([1, 2, 1])
with cols_top[1]:
    if hasattr(st, "page_link"):
        st.page_link("main.py", label="⬅️ main画面へ戻る", icon="🏠", width="stretch")
    else:
        if st.button("⬅️ main画面へ戻る", width="stretch"):
            try:
                if hasattr(st, "switch_page"):
                    st.switch_page("main.py")
                else:
                    st.experimental_set_query_params()
                    st.experimental_rerun()
            except Exception:
                pass
