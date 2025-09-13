import sqlite3
import pandas as pd
from pathlib import Path
import time
import streamlit as st

# 定数
PLAYER_CSV = 'players.csv'
DATA_DIR = Path.cwd() / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "events.db"

POINT_MAP = {'3pt': 3, '2pt': 2, '1pt': 1}
STAT_SET = {'アシスト', 'ブロック', 'リバウンド', 'スティール'}
FOUL_SET = {'ファール', 'ターンオーバー'}

# 共有CSS

def inject_css():
    st.markdown("""
    <style>
    .stButton > button { height:64px; font-size:20px; border-radius:14px; padding:12px 18px; }
    label { font-size:16px !important; }
    .block-container { padding-top:0.4rem; padding-bottom:4rem; }
    .scorebar { position: sticky; top: 0; z-index: 999; background: #ffffffcc; backdrop-filter: blur(4px);
                padding: 8px 12px; border-bottom: 1px solid #eee; border-radius: 0 0 10px 10px; }
    .scorebox { display:flex; gap:12px; align-items:center; justify-content:space-between; }
    .scorechip { display:inline-block; padding:6px 14px; border-radius: 999px; font-weight:700; }
    .red { background:#ffe5e5; border:1px solid #ffb3b3; }
    .blue{ background:#e5f0ff; border:1px solid #b3d0ff; }
    .info { font-size:14px; color:#666; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_resource
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=3000;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class TEXT,
            team TEXT,
            bib TEXT,
            no TEXT,
            name TEXT,
            action TEXT,
            quarter TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ct ON events(class, team)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at)")
    return conn


@st.cache_data
def load_players(updated_at: float = 0) -> pd.DataFrame:
    p = Path(PLAYER_CSV)
    if not p.exists():
        return pd.DataFrame(columns=['CLASS', 'TEAM', '背番号', 'プレイヤー名', 'ビブスType', '表示'])
    df = pd.read_csv(p, dtype=str)
    for c in ['CLASS', 'TEAM', '背番号', 'プレイヤー名', 'ビブスType']:
        if c not in df.columns:
            df[c] = ''
    df['背番号'] = df['背番号'].astype(str)
    df['表示'] = df['背番号'] + ' - ' + df['プレイヤー名'] + ' - ' + df['ビブスType']
    return df


def notify(msg: str, icon: str = "✅"):
    if hasattr(st, "toast"):
        st.toast(msg, icon=icon)
    else:
        st.success(msg)


def add_event_sql(conn, classType, team, bibsType, uniformNumber, playerName, action_label, quarter):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events(class,team,bib,no,name,action,quarter) VALUES (?,?,?,?,?,?,?)",
        (classType, team, bibsType, uniformNumber, playerName, action_label, quarter)
    )
    conn.commit()
    return cur.lastrowid


def delete_event_by_id(conn, row_id: int):
    conn.execute("DELETE FROM events WHERE id=?", (row_id,))
    conn.commit()


def delete_events_by_ids(conn, ids):
    if not ids:
        return
    placeholders = ",".join(["?"] * len(ids))
    conn.execute(f"DELETE FROM events WHERE id IN ({placeholders})", ids)
    conn.commit()


def read_df_sql(conn) -> pd.DataFrame:
    return pd.read_sql_query("""
        SELECT class AS CLASS, team AS TEAM, bib AS ビブスType, no AS 背番号, name AS 名前,
               action AS "得点・アシスト", quarter AS クォーター, created_at, id
        FROM events
        ORDER BY id
    """, conn)


def read_recent_df(conn, n=30) -> pd.DataFrame:
    df = pd.read_sql_query(f"""
        SELECT class AS CLASS, team AS TEAM, bib AS ビブスType, no AS 背番号, name AS 名前,
               action AS "得点・アシスト", quarter AS クォーター, created_at, id
        FROM events
        ORDER BY id DESC
        LIMIT {int(n)}
    """, conn)
    return df[::-1]


def export_events_csv(conn):
    df = read_df_sql(conn)
    fname = f"events_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    csv_bytes = df.drop(columns=['id']).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    return fname, csv_bytes


def backup_sqlite(conn):
    backups_dir = DATA_DIR / "backups"
    backups_dir.mkdir(exist_ok=True)
    fname = f"events_backup_{time.strftime('%Y%m%d_%H%M%S')}.db"
    dst_path = backups_dir / fname
    with sqlite3.connect(dst_path) as dst:
        conn.backup(dst)
    with open(dst_path, "rb") as f:
        data = f.read()
    return fname, data


def wipe_all_data(conn):
    conn.execute("BEGIN IMMEDIATE;")
    conn.execute("DELETE FROM events;")
    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name='events';")
    except sqlite3.Error:
        pass
    conn.commit()
    try:
        conn.execute("VACUUM;")
    except sqlite3.Error:
        pass


def get_score_red_blue(conn):
    df = read_df_sql(conn)
    if df.empty:
        return (0, 0)
    score_df = df[df['得点・アシスト'].isin(POINT_MAP.keys())].copy()
    if score_df.empty:
        return (0, 0)
    score_df['得点'] = score_df['得点・アシスト'].map(POINT_MAP)
    gp = score_df.groupby('TEAM', as_index=False)['得点'].sum()
    red = int(gp.loc[gp['TEAM'] == 'Red', '得点'].sum()) if 'Red' in gp['TEAM'].values else 0
    blue = int(gp.loc[gp['TEAM'] == 'Blue', '得点'].sum()) if 'Blue' in gp['TEAM'].values else 0
    return (red, blue)


def inject_mobile_big_ui():
    st.markdown("""
    <style>
    .stButton > button {
      width: 100%;
      height: 88px;
      font-size: 22px;
      font-weight: 700;
      border-radius: 18px;
      padding: 16px 20px;
    }
    a[data-testid="stLinkButton"] {
      display: block;
      text-align: center;
      padding: 16px 18px;
      border-radius: 18px;
      font-size: 20px;
      font-weight: 700;
      text-decoration: none !important;
    }
    .scorechip { font-size: 18px; padding: 8px 16px; }
    label { font-size: 18px !important; }
    div[role="radiogroup"] label { margin-right: 10px; }
    div[data-testid="stDataFrame"] * { font-size: 15px; }
    @media (max-width: 640px){
      .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
      .stButton > button { height: 96px; font-size: 24px; }
    }
    </style>
    """, unsafe_allow_html=True)