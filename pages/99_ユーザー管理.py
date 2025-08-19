# pages/99_ユーザー管理.py
import streamlit as st
import pandas as pd

# 最初の1回だけ page_config
if not st.session_state.get("_pc_set", False):
    try:
        st.set_page_config(page_title="👑 ユーザー管理", layout="centered", initial_sidebar_state="expanded")
    except Exception:
        pass
    st.session_state["_pc_set"] = True

from lib_db import get_conn, inject_css, inject_mobile_big_ui
from auth import (
    ensure_users_table, require_login, require_admin, render_userbox,
    list_users, create_user, change_username, admin_set_password, admin_delete_user,
    get_current_user
)

# 共通UI
inject_css()
inject_mobile_big_ui()

# 認証・権限
require_login()
require_admin()
render_userbox()

st.title("👑 ユーザー管理")

# 内部遷移（mainへ戻る）推奨ボタン
has_pagelink = hasattr(st, "page_link")
cols_top = st.columns([1, 2, 1])
with cols_top[1]:
    if has_pagelink:
        st.page_link("main.py", label="⬅️ main画面へ戻る", icon="🏠", use_container_width=True)
    else:
        if st.button("⬅️ main画面へ戻る", use_container_width=True):
            try:
                if hasattr(st, "switch_page"):
                    st.switch_page("main.py")
                else:
                    st.experimental_set_query_params()  # ?page をクリア
                    st.experimental_rerun()
            except Exception:
                pass

# DB 準備
conn = get_conn()
ensure_users_table(conn)
me = get_current_user()

# ユーザー一覧
rows = list_users(conn)  # [(id, username, role, created_at), ...]
df = pd.DataFrame(rows, columns=["id", "username", "role", "created_at"]) if rows else pd.DataFrame(columns=["id","username","role","created_at"])

st.subheader("👥 ユーザー一覧")
if df.empty:
    st.info("ユーザーがいません。まずは『ユーザー追加』から作成してください。")
else:
    # 簡易フィルタ
    with st.expander("🔎 フィルタ", expanded=False):
        q = st.text_input("ユーザー名で絞り込み（部分一致）", value="", key="user_filter_q")
        role_pick = st.selectbox("ロールで絞り込み", ("すべて", "admin", "user"), key="user_filter_role")
    view = df.copy()
    if q.strip():
        view = view[view["username"].str.contains(q.strip(), na=False)]
    if role_pick != "すべて":
        view = view[view["role"] == role_pick]
    st.dataframe(view.sort_values(["id"]), use_container_width=True, height=280)

st.markdown("---")

# 2カラム：左=ユーザー追加、右=既存ユーザー管理
col_add, col_edit = st.columns(2)

# ➊ ユーザー追加
with col_add:
    st.subheader("➕ ユーザー追加")
    with st.form("add_user"):
        new_u = st.text_input("ユーザー名", key="add_user_name")
        new_p1 = st.text_input("パスワード", type="password", key="add_user_pw1")
        new_p2 = st.text_input("パスワード（確認）", type="password", key="add_user_pw2")
        new_role = st.selectbox("ロール", ["user", "admin"], key="add_user_role")
        ok_add = st.form_submit_button("作成", use_container_width=True)
    if ok_add:
        if not new_u or not new_p1:
            st.error("ユーザー名／パスワードは必須です。")
        elif new_p1 != new_p2:
            st.error("確認用パスワードが一致しません。")
        else:
            ok, msg = create_user(conn, new_u, new_p1, role=new_role)
            (st.success if ok else st.error)(msg)
            if ok:
                try: st.rerun()
                except Exception:
                    try: st.experimental_rerun()
                    except Exception: pass

# ➋ 既存ユーザー管理（編集・PWリセット・削除）
with col_edit:
    st.subheader("🛠️ 既存ユーザー管理")

    if df.empty:
        st.info("ユーザーがいません。")
    else:
        # 選択肢（id: username (role)）
        options = [f"{int(r.id)}: {r.username} ({r.role})" for _, r in df.sort_values("id").iterrows()]
        pick = st.selectbox("対象ユーザーを選択", options, key="edit_user_pick")
        # 取り出し
        sel_id = int(pick.split(":")[0]) if pick else None
        sel_row = df[df["id"] == sel_id].iloc[0] if sel_id in df["id"].values else None

        if sel_row is not None:
            st.markdown(f"**選択中:** ID={int(sel_row.id)} / {sel_row.username} / role={sel_row.role}")

            # a) ユーザー名変更
            with st.form("edit_username"):
                new_name = st.text_input("新しいユーザー名", value=sel_row.username, key="edit_username_value")
                ok_uname = st.form_submit_button("✏️ ユーザー名を変更", use_container_width=True)
            if ok_uname:
                ok, msg = change_username(conn, user_id=int(sel_row.id), new_username=new_name)
                (st.success if ok else st.error)(msg)
                if ok:
                    try: st.rerun()
                    except Exception:
                        try: st.experimental_rerun()
                        except Exception: pass

            st.markdown("")

            # b) ロール変更（ページ内で直接UPDATE）
            with st.form("edit_role"):
                role_new = st.selectbox("ロールを変更", ["user", "admin"], index=0 if sel_row.role == "user" else 1, key="edit_role_value")
                ok_role = st.form_submit_button("🔁 ロールを変更", use_container_width=True)
            if ok_role:
                try:
                    conn.execute("UPDATE users SET role=? WHERE id=?", (role_new, int(sel_row.id)))
                    conn.commit()
                    st.success("ロールを変更しました。")
                    try: st.rerun()
                    except Exception:
                        try: st.experimental_rerun()
                        except Exception: pass
                except Exception as e:
                    st.error(f"ロール変更に失敗しました: {e}")

            st.markdown("")

            # c) パスワードリセット（管理者が強制）
            with st.form("reset_pw"):
                pw1 = st.text_input("新しいパスワード", type="password", key="reset_pw1")
                pw2 = st.text_input("新しいパスワード（確認）", type="password", key="reset_pw2")
                ok_pw = st.form_submit_button("🔐 パスワードをリセット", use_container_width=True)
            if ok_pw:
                if pw1 != pw2:
                    st.error("確認用パスワードが一致しません。")
                else:
                    ok, msg = admin_set_password(conn, int(sel_row.id), pw1)
                    (st.success if ok else st.error)(msg)

            st.markdown("")

            # d) ユーザー削除（自分自身は不可）
            with st.form("delete_user"):
                st.warning("⚠️ この操作は取り消せません。")
                confirm_txt = st.text_input(f"確認用に「DELETE {int(sel_row.id)}」と入力してください", key="delete_confirm_txt")
                ok_del = st.form_submit_button("🗑️ ユーザーを削除", use_container_width=True)
            if ok_del:
                if confirm_txt.strip() == f"DELETE {int(sel_row.id)}":
                    ok, msg = admin_delete_user(conn, int(sel_row.id), acting_user_id=int(me["id"]))
                    (st.success if ok else st.error)(msg)
                    if ok:
                        try: st.rerun()
                        except Exception:
                            try: st.experimental_rerun()
                            except Exception: pass
                else:
                    st.error("確認文字が一致しません。")
