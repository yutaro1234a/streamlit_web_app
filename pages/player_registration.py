import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from app_auth import require_login, render_userbox


# =========================
# 認証
# =========================
require_login()
try:
    
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] a[href*="_login"],
        [data-testid="stSidebarNav"] a[href*="%5Flogin"],
        [data-testid="stSidebarNav"] a[href*="login"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
    render_userbox(key="logout_button_register")
except TypeError:
    render_userbox()


# =========================
# 定数
# =========================
DB_PATH = "players.db"
JSON_PATH = Path("players.json")

PLAYER_COLUMNS = [
    "id",
    "uniform_number",
    "player_name",
    "team",
    "bibs_type",
    "class_type",
]


# =========================
# 共通ユーティリティ
# =========================
def normalize_player_df(df):
    """不足カラムを補い、表示・保存に必要な列順を整える。"""
    if df is None or df.empty:
        return pd.DataFrame(columns=PLAYER_COLUMNS)

    df = df.copy()
    for col in PLAYER_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[PLAYER_COLUMNS]


def next_json_id(df):
    """JSON保存時の次IDを採番する。"""
    if df.empty or "id" not in df.columns:
        return 1

    numeric_ids = pd.to_numeric(df["id"], errors="coerce").dropna()
    if numeric_ids.empty:
        return 1

    return int(numeric_ids.max()) + 1


def safe_rerun():
    try:
        st.rerun()
    except Exception:
        st.warning("🔄 手動でページを再読み込みしてください")


# =========================
# JSON操作
# ※ init_json より先に定義することが重要
# =========================
def save_players_json(df):
    """players.json に選手一覧を保存する。"""
    df = normalize_player_df(df)
    data = df.to_dict(orient="records")

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_players_json():
    """players.json から選手一覧を読み込む。存在しなければ空で作成する。"""
    if not JSON_PATH.exists():
        save_players_json(pd.DataFrame(columns=PLAYER_COLUMNS))

    try:
        with JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            st.warning("⚠️ players.json の形式が不正です。空データとして扱います。")
            return pd.DataFrame(columns=PLAYER_COLUMNS)

        return normalize_player_df(pd.DataFrame(data))
    except Exception as e:
        st.error(f"❌ JSONファイルの読み込みに失敗しました: {e}")
        return pd.DataFrame(columns=PLAYER_COLUMNS)


def init_json():
    """初回起動時に players.json を作成する。"""
    if not JSON_PATH.exists():
        save_players_json(pd.DataFrame(columns=PLAYER_COLUMNS))


def save_player_json(uniform_number, player_name, team, bibs_type, class_type):
    """JSONへ選手を登録する。重複データは登録しない。"""
    df = load_players_json()

    duplicate = df[
        (df["uniform_number"].astype(str) == str(uniform_number))
        & (df["player_name"].astype(str) == str(player_name))
        & (df["team"].astype(str) == str(team))
        & (df["bibs_type"].astype(str) == str(bibs_type))
        & (df["class_type"].astype(str) == str(class_type))
    ]

    if not duplicate.empty:
        return False

    new_row = {
        "id": next_json_id(df),
        "uniform_number": str(uniform_number),
        "player_name": str(player_name),
        "team": str(team),
        "bibs_type": str(bibs_type),
        "class_type": str(class_type),
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_players_json(df)
    return True


def delete_player_json(player_id):
    """JSONから指定IDの選手を削除する。"""
    df = load_players_json()
    df = df[pd.to_numeric(df["id"], errors="coerce") != int(player_id)]
    save_players_json(df)


# =========================
# SQLite操作
# =========================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uniform_number TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                bibs_type TEXT NOT NULL,
                class_type TEXT NOT NULL,
                UNIQUE(uniform_number, player_name, team, bibs_type, class_type)
            );
            """
        )
        conn.commit()


def fetch_players_sqlite():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM players", conn)
    return normalize_player_df(df)


def save_player_sqlite(uniform_number, player_name, team, bibs_type, class_type):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            before = conn.total_changes
            conn.execute(
                """
                INSERT OR IGNORE INTO players
                (uniform_number, player_name, team, bibs_type, class_type)
                VALUES (?, ?, ?, ?, ?);
                """,
                (uniform_number, player_name, team, bibs_type, class_type),
            )
            conn.commit()
            after = conn.total_changes
        return after > before
    except Exception as e:
        st.error(f"❌ 登録中にエラーが発生しました: {e}")
        return False


def delete_player_sqlite(player_id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
            conn.commit()
    except Exception as e:
        st.error(f"❌ 削除中にエラーが発生しました: {e}")


# =========================
# SQLite / JSON 連携
# =========================
def export_sqlite_to_json():
    df = fetch_players_sqlite()
    save_players_json(df)


def import_json_to_sqlite():
    df = load_players_json()
    if df.empty:
        return 0

    inserted_count = 0
    with sqlite3.connect(DB_PATH) as conn:
        for _, row in df.iterrows():
            before = conn.total_changes
            conn.execute(
                """
                INSERT OR IGNORE INTO players
                (uniform_number, player_name, team, bibs_type, class_type)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    str(row.get("uniform_number", "")),
                    str(row.get("player_name", "")),
                    str(row.get("team", "")),
                    str(row.get("bibs_type", "")),
                    str(row.get("class_type", "")),
                ),
            )
            if conn.total_changes > before:
                inserted_count += 1
        conn.commit()

    return inserted_count


# =========================
# 初期化
# =========================
init_db()
init_json()


# =========================
# デザインCSS
# =========================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 8% 8%, rgba(37, 99, 235, .16), transparent 28%),
        radial-gradient(circle at 94% 12%, rgba(6, 182, 212, .20), transparent 30%),
        radial-gradient(circle at 20% 90%, rgba(239, 68, 68, .10), transparent 26%),
        linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

.block-container {
    padding-top: 1.3rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}

.page-hero {
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    padding: 30px 32px;
    margin: 6px 0 18px 0;
    color: #fff;
    background:
        radial-gradient(circle at 16% 0%, rgba(255,255,255,.34), transparent 28%),
        radial-gradient(circle at 88% 22%, rgba(56,189,248,.34), transparent 26%),
        linear-gradient(135deg, #020617 0%, #0f172a 45%, #1e3a8a 100%);
    box-shadow: 0 24px 65px rgba(15, 23, 42, .28);
}

.page-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.08) 1px, transparent 1px);
    background-size: 34px 34px;
    mask-image: linear-gradient(90deg, rgba(0,0,0,.8), transparent 80%);
}

.page-hero::after {
    content: "👟";
    position: absolute;
    right: 30px;
    top: 20px;
    font-size: 82px;
    opacity: .15;
    transform: rotate(-12deg);
}

.hero-kicker {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.25);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .06em;
    margin-bottom: 13px;
    backdrop-filter: blur(10px);
}

.hero-title {
    position: relative;
    font-size: clamp(30px, 4vw, 44px);
    font-weight: 950;
    line-height: 1.12;
    margin: 0;
}

.hero-subtitle {
    position: relative;
    color: rgba(255,255,255,.78);
    font-size: 14px;
    margin-top: 10px;
}

.storage-card,
.form-card,
.list-card,
.delete-card,
.metric-card {
    border-radius: 26px;
    padding: 20px 22px;
    background: rgba(255,255,255,.86);
    border: 1px solid rgba(255,255,255,.90);
    box-shadow: 0 16px 42px rgba(15, 23, 42, .09);
    backdrop-filter: blur(14px);
    margin: 16px 0;
}

.storage-card,
.metric-card {
    position: relative;
    overflow: hidden;
}

.storage-card::before,
.metric-card::before {
    content: "";
    position: absolute;
    inset: 0 auto 0 0;
    width: 7px;
    background: linear-gradient(180deg, #2563eb, #06b6d4);
}

.card-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 20px;
    font-weight: 950;
    color: #0f172a;
    margin-bottom: 4px;
}

.card-desc {
    color: #64748b;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 14px;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
    margin: 10px 0 4px 0;
}

.metric-label {
    color: #64748b;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .06em;
}

.metric-value {
    color: #0f172a;
    font-size: 32px;
    font-weight: 950;
    line-height: 1.1;
    margin-top: 6px;
    font-variant-numeric: tabular-nums;
}

.metric-note {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 800;
    margin-top: 6px;
}

div[data-baseweb="select"] > div,
input,
textarea {
    border-radius: 16px !important;
    border-color: #dbe3ef !important;
    box-shadow: 0 7px 18px rgba(15, 23, 42, .055) !important;
    background-color: rgba(255,255,255,.94) !important;
}

.stTextInput label,
.stSelectbox label,
.stRadio label,
.stCheckbox label {
    font-weight: 900 !important;
    color: #334155 !important;
}

div[data-testid="stFormSubmitButton"] button,
div.stButton > button {
    border-radius: 999px !important;
    min-height: 46px;
    font-weight: 950 !important;
    border: 1px solid rgba(15, 23, 42, .08) !important;
    background: linear-gradient(135deg, #2563eb, #06b6d4) !important;
    color: white !important;
    box-shadow: 0 12px 26px rgba(37, 99, 235, .25) !important;
    transition: transform .16s ease, box-shadow .16s ease;
}

div[data-testid="stFormSubmitButton"] button:hover,
div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 16px 34px rgba(37, 99, 235, .32) !important;
    color: white !important;
}

.delete-card div.stButton > button {
    background: linear-gradient(135deg, #dc2626, #fb7185) !important;
    box-shadow: 0 12px 26px rgba(220, 38, 38, .20) !important;
}

[data-testid="stDataFrame"] {
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid rgba(226,232,240,.92);
    box-shadow: 0 10px 26px rgba(15, 23, 42, .055);
}

[data-testid="stDataFrame"] [role="columnheader"] {
    background: #f8fafc !important;
    color: #0f172a !important;
    font-weight: 900 !important;
}

hr {
    opacity: .42;
}

@media (max-width: 800px) {
    .metric-grid {
        grid-template-columns: 1fr;
    }
    .page-hero {
        padding: 22px 18px;
        border-radius: 24px;
    }
    .page-hero::after {
        display: none;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# ヘッダー
# =========================
st.markdown(
    """
<div class="page-hero">
    <div class="hero-kicker">🏀 PLAYER MANAGEMENT</div>
    <div class="hero-title">選手登録</div>
    <div class="hero-subtitle">背番号・名前・チーム・ビブスType・CLASSを登録・管理します。</div>
</div>
""",
    unsafe_allow_html=True,
)


# =========================
# 保存方式選択
# =========================
st.markdown(
    """
<div class="storage-card">
    <div class="card-title">💾 データ保存方式</div>
    <div class="card-desc">サーバ再起動でSQLiteが消える環境では、JSONを選択してください。</div>
</div>
""",
    unsafe_allow_html=True,
)

storage_type = st.radio(
    "保存・読み込み先",
    options=["JSON", "SQLite"],
    horizontal=True,
    help="JSONは players.json、SQLiteは players.db に保存します。",
)

sync_col1, sync_col2 = st.columns(2)
with sync_col1:
    if st.button("📤 SQLite → JSONへ書き出し", key="export_sqlite_json"):
        export_sqlite_to_json()
        st.success("✅ SQLiteの選手データを players.json に書き出しました。")

with sync_col2:
    if st.button("📥 JSON → SQLiteへ取り込み", key="import_json_sqlite"):
        count = import_json_to_sqlite()
        st.success(f"✅ JSONからSQLiteへ取り込みました。追加件数: {count}件")


# =========================
# 現在データ取得
# =========================
def fetch_players():
    if storage_type == "JSON":
        return load_players_json()
    return fetch_players_sqlite()


df = fetch_players()

red_count = int((df["team"] == "Red").sum()) if not df.empty else 0
blue_count = int((df["team"] == "Blue").sum()) if not df.empty else 0

st.markdown(
    f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-label">TOTAL PLAYERS</div>
        <div class="metric-value">{len(df)}</div>
        <div class="metric-note">登録済み選手数</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">TEAM RED</div>
        <div class="metric-value">{red_count}</div>
        <div class="metric-note">Red所属</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">TEAM BLUE</div>
        <div class="metric-value">{blue_count}</div>
        <div class="metric-note">Blue所属</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# =========================
# 新規登録
# =========================
st.markdown(
    """
<div class="form-card">
    <div class="card-title">📝 新規選手登録</div>
    <div class="card-desc">登録したい選手情報を入力してください。</div>
</div>
""",
    unsafe_allow_html=True,
)

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

if submit:
    uniform_number = uniform_number.strip()
    player_name = player_name.strip()

    if uniform_number and player_name:
        if storage_type == "JSON":
            inserted = save_player_json(uniform_number, player_name, team, bibs_type, class_type)
        else:
            inserted = save_player_sqlite(uniform_number, player_name, team, bibs_type, class_type)

        if inserted:
            st.success(f"🎉 選手 {player_name}（背番号: {uniform_number}）を登録しました！")
        else:
            st.info("ℹ️ 同じ選手情報が既に登録されています。")
        safe_rerun()
    else:
        st.warning("⚠️ 背番号とプレイヤー名は必須です")


# =========================
# 一覧表示
# =========================
df = fetch_players()

st.markdown(
    """
<div class="list-card">
    <div class="card-title">📋 登録済み選手一覧</div>
    <div class="card-desc">現在登録されている選手を確認できます。</div>
</div>
""",
    unsafe_allow_html=True,
)

if not df.empty:
    df_show = df.drop(columns=["id"], errors="ignore")
    st.dataframe(df_show, width="stretch", hide_index=True)
else:
    st.info("まだ選手は登録されていません。")


# =========================
# 削除
# =========================
if not df.empty:
    st.markdown(
        """
<div class="delete-card">
    <div class="card-title">🗑️ 選手の削除</div>
    <div class="card-desc">削除対象を選択して、確認チェック後に削除してください。</div>
</div>
""",
        unsafe_allow_html=True,
    )

    player_options = {
        f"{row['uniform_number']} - {row['player_name']} - {row['team']} - {row['bibs_type']} - {row['class_type']}": int(row["id"])
        for _, row in df.iterrows()
    }

    selected_id = st.selectbox(
        "削除する選手を選択",
        options=list(player_options.values()),
        format_func=lambda x: [k for k, v in player_options.items() if v == x][0],
        key="delete_select",
    )

    confirm = st.checkbox("⚠️ 本当にこの選手を削除しますか？", key="confirm_delete")

    if st.button("❌ この選手を削除", key="delete_button"):
        if confirm:
            if storage_type == "JSON":
                delete_player_json(selected_id)
            else:
                delete_player_sqlite(selected_id)
            st.success("✅ 選手を削除しました！")
            safe_rerun()
        else:
            st.warning("⚠️ 削除する場合は確認チェックを入れてください。")
