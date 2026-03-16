import os, hashlib, hmac, sqlite3
from typing import Optional, Tuple, Dict
import streamlit as st
from lib_db import get_conn

_ITER = 200_000

def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITER)
    return f"pbkdf2_sha256${_ITER}${salt.hex()}${dk.hex()}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        iters = int(iters)
        salt = bytes.fromhex(salt_hex)
        new_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
        return hmac.compare_digest(new_dk.hex(), hash_hex)
    except Exception:
        return False

def ensure_users_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          pw_hash TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT 'user',
          created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()

def users_count(conn: sqlite3.Connection) -> int:
    cur = conn.execute("SELECT COUNT(*) FROM users;")
    return int(cur.fetchone()[0])

def create_user(conn: sqlite3.Connection, username: str, password: str, role: str = "user") -> Tuple[bool, str]:
    try:
        pw_hash = _hash_password(password)
        conn.execute("INSERT INTO users (username, pw_hash, role) VALUES (?, ?, ?);",
                     (username, pw_hash, role))
        conn.commit()
        return True, "ユーザーを作成しました。"
    except sqlite3.IntegrityError:
        return False, "そのユーザー名は既に存在します。"
    except Exception as e:
        return False, f"作成に失敗しました: {e}"

def authenticate(conn: sqlite3.Connection, username: str, password: str) -> Optional[Dict]:
    row = conn.execute("SELECT id, username, pw_hash, role FROM users WHERE username=?;", (username,)).fetchone()
    if not row:
        return None
    if _verify_password(password, row[2]):
        return {"id": row[0], "username": row[1], "role": row[3]}
    return None

def get_current_user() -> Optional[Dict]:
    return st.session_state.get("auth_user")

def refresh_session_user(conn: sqlite3.Connection, user_id: int) -> None:
    row = conn.execute("SELECT id, username, role FROM users WHERE id=?;", (user_id,)).fetchone()
    if row:
        st.session_state["auth_user"] = {"id": row[0], "username": row[1], "role": row[2]}

def require_login() -> None:
    if st.session_state.get("auth_user"):
        return
    try:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/00_ログイン.py")
            return
    except Exception:
        pass
    st.warning("このページを表示するにはログインが必要です。")
    st.markdown('<a href="/?page=00_%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3" target="_self">➡️ ログインページへ</a>', unsafe_allow_html=True)
    st.stop()

def require_admin() -> None:
    user = get_current_user()
    if not user:
        require_login()
        return
    if user.get("role") != "admin":
        st.error("このページは管理者のみ利用できます。")
        st.stop()

def render_userbox(key: str = "logout_button_default") -> None:
    user = st.session_state.get("auth_user")
    with st.sidebar:
        if user:
            st.caption("ログイン中")
            st.markdown(f"**{user['username']}**（{user['role']}）")
            if st.button("🚪 ログアウト", width='stretch', key=key):
                st.session_state.pop("auth_user", None)
                try:
                    if hasattr(st, "switch_page"):
                        st.switch_page("pages/00_ログイン.py")
                        return
                except Exception:
                    pass
                st.rerun()
        else:
            st.caption("未ログイン")

def change_password(conn: sqlite3.Connection, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
    row = conn.execute("SELECT pw_hash FROM users WHERE id=?;", (user_id,)).fetchone()
    if not row:
        return False, "ユーザーが見つかりません。"
    if not _verify_password(current_password, row[0]):
        return False, "現在のパスワードが正しくありません。"
    if len(new_password) < 6:
        return False, "新しいパスワードは6文字以上にしてください。"
    new_hash = _hash_password(new_password)
    conn.execute("UPDATE users SET pw_hash=? WHERE id=?;", (new_hash, user_id))
    conn.commit()
    return True, "パスワードを変更しました。"

def change_username(conn: sqlite3.Connection, user_id: int, new_username: str) -> Tuple[bool, str]:
    new_username = (new_username or "").strip()
    if not new_username:
        return False, "ユーザー名を入力してください。"
    row = conn.execute("SELECT id FROM users WHERE username=?;", (new_username,)).fetchone()
    if row and int(row[0]) != int(user_id):
        return False, "そのユーザー名は既に使われています。"
    conn.execute("UPDATE users SET username=? WHERE id=?;", (new_username, user_id))
    conn.commit()
    refresh_session_user(conn, user_id)
    return True, "ユーザー名を変更しました。"

def admin_set_password(conn: sqlite3.Connection, target_user_id: int, new_password: str) -> Tuple[bool, str]:
    if len(new_password) < 6:
        return False, "新しいパスワードは6文字以上にしてください。"
    new_hash = _hash_password(new_password)
    cur = conn.execute("UPDATE users SET pw_hash=? WHERE id=?;", (new_hash, target_user_id))
    if cur.rowcount == 0:
        return False, "対象ユーザーが見つかりません。"
    conn.commit()
    return True, "パスワードをリセットしました。"

def admin_delete_user(conn: sqlite3.Connection, target_user_id: int, acting_user_id: int) -> Tuple[bool, str]:
    if int(target_user_id) == int(acting_user_id):
        return False, "自分自身は削除できません。"
    cur = conn.execute("DELETE FROM users WHERE id=?;", (target_user_id,))
    if cur.rowcount == 0:
        return False, "対象ユーザーが見つかりません。"
    conn.commit()
    return True, "ユーザーを削除しました。"

def list_users(conn: sqlite3.Connection):
    return conn.execute("SELECT id, username, role, created_at FROM users ORDER BY id;").fetchall()
