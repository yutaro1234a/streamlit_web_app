# auth.py
import os, hashlib, hmac, sqlite3, time
import streamlit as st
from typing import Optional, Tuple
from lib_db import get_conn

# ---- パスワードハッシュ（PBKDF2-SHA256） ----
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

# ---- users テーブル ----
def ensure_users_table(conn: sqlite3.Connection):
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

def users_count(conn) -> int:
    cur = conn.execute("SELECT COUNT(*) FROM users;")
    return int(cur.fetchone()[0])

def create_user(conn, username: str, password: str, role: str = "user") -> Tuple[bool, str]:
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

def authenticate(conn, username: str, password: str) -> Optional[dict]:
    row = conn.execute("SELECT id, username, pw_hash, role FROM users WHERE username=?;", (username,)).fetchone()
    if not row:
        return None
    if _verify_password(password, row[2]):
        return {"id": row[0], "username": row[1], "role": row[3]}
    return None

# ---- UIヘルパー：ログイン必須＆ログアウト ----
def require_login():
    """未ログインならログインページへ誘導して停止"""
    if st.session_state.get("auth_user"):
        return
    # できれば自動遷移
    try:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/00_ログイン.py")
    except Exception:
        pass
    # フォールバック（同一タブでリンク表示）
    st.warning("このページを表示するにはログインが必要です。")
    st.markdown('<a href="/?page=00_%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3" target="_self">➡️ ログインページへ</a>', unsafe_allow_html=True)
    st.stop()

def render_userbox():
    """サイドバーにユーザー情報＆ログアウト"""
    user = st.session_state.get("auth_user")
    with st.sidebar:
        if user:
            st.caption("ログイン中")
            st.markdown(f"**{user['username']}**（{user['role']}）")
            if st.button("🚪 ログアウト", use_container_width=True):
                st.session_state.pop("auth_user", None)
                # ログインへ
                try:
                    if hasattr(st, "switch_page"):
                        st.switch_page("pages/00_ログイン.py")
                        return
                except Exception:
                    pass
                st.experimental_set_query_params(page="00_ログイン")
                try: st.rerun()
                except Exception: pass
        else:
            st.caption("未ログイン")
