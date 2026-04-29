# pages/01_集計.py

import json
import sqlite3
import textwrap
from pathlib import Path

import pandas as pd
import streamlit as st

from app_auth import require_login, render_userbox


# =========================
# ページ設定
# =========================
st.set_page_config(page_title="📊 スコア集計", layout="wide")

require_login()
render_userbox()


# =========================
# 定数
# =========================
DATA_FILE = Path("score_sheet_data.json")
PLAYERS_DB_PATH = "players.db"

POINT_MAP = {
    "": 0,
    "1点": 1,
    "2点": 2,
    "3点": 3,
}

CLASS_ORDER = ["初級", "中級", "上級"]


def render_html(content):
    """HTMLを1行に圧縮して、Markdownのコードブロック扱いを防ぐ。"""
    html = "".join(line.strip() for line in textwrap.dedent(content).splitlines() if line.strip())
    st.markdown(html, unsafe_allow_html=True)



# =========================
# デザインCSS
# =========================
def inject_style():
    render_html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700;800;900&display=swap');

        :root {
            --card: rgba(255, 255, 255, .84);
            --line: rgba(226, 232, 240, .88);
            --text: #0f172a;
            --muted: #64748b;
        }

        html, body, [class*="css"] {
            font-family: 'Noto Sans JP', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 8%, rgba(239, 68, 68, .14), transparent 28%),
                radial-gradient(circle at 92% 12%, rgba(37, 99, 235, .16), transparent 30%),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }

        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            max-width: 1220px;
        }

        h1, h2, h3 { letter-spacing: .02em; }

        div[data-testid="stVerticalBlock"] { gap: .8rem; }

        .summary-hero {
            position: relative;
            overflow: hidden;
            border-radius: 30px;
            padding: 28px 30px;
            margin: 6px 0 18px 0;
            color: #fff;
            background:
                radial-gradient(circle at 18% 0%, rgba(255,255,255,.32), transparent 28%),
                radial-gradient(circle at 82% 18%, rgba(96,165,250,.42), transparent 24%),
                linear-gradient(135deg, #0f172a 0%, #1e293b 48%, #334155 100%);
            box-shadow: 0 22px 60px rgba(15, 23, 42, .26);
            isolation: isolate;
        }

        .summary-hero::before {
            content: "";
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(255,255,255,.08) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,.08) 1px, transparent 1px);
            background-size: 34px 34px;
            mask-image: linear-gradient(90deg, rgba(0,0,0,.7), transparent 78%);
            z-index: -1;
        }

        .summary-hero::after {
            content: "🏀";
            position: absolute;
            right: 28px;
            top: 22px;
            font-size: 74px;
            opacity: .18;
            transform: rotate(-12deg);
        }

        .hero-kicker {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,.16);
            border: 1px solid rgba(255,255,255,.24);
            font-size: 12px;
            font-weight: 900;
            margin-bottom: 12px;
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

        .score-board {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 130px minmax(0, 1fr);
            gap: 14px;
            margin: 12px 0 14px 0;
            align-items: stretch;
        }

        .score-card {
            min-width: 0;
            position: relative;
            overflow: hidden;
            border-radius: 26px;
            padding: 20px 20px 18px 20px;
            background: var(--card);
            border: 1px solid rgba(255,255,255,.78);
            box-shadow: 0 16px 38px rgba(15, 23, 42, .11);
            text-align: center;
            backdrop-filter: blur(14px);
        }

        .score-card::before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 7px;
        }

        .score-card::after {
            content: "";
            position: absolute;
            right: -46px;
            bottom: -60px;
            width: 150px;
            height: 150px;
            border-radius: 999px;
            opacity: .08;
        }

        .score-card.red::before { background: linear-gradient(90deg, #ef4444, #fb7185); }
        .score-card.blue::before { background: linear-gradient(90deg, #2563eb, #38bdf8); }
        .score-card.red::after { background: #ef4444; }
        .score-card.blue::after { background: #2563eb; }

        .score-card.winner {
            border-color: rgba(245, 158, 11, .75);
            box-shadow: 0 18px 44px rgba(245, 158, 11, .22);
            transform: translateY(-1px);
        }

        .score-team-label {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            padding: 5px 13px;
            font-size: 11px;
            font-weight: 950;
            color: #fff;
            letter-spacing: .08em;
            margin-bottom: 9px;
        }

        .red-label { background: linear-gradient(135deg, #dc2626, #fb7185); }
        .blue-label { background: linear-gradient(135deg, #2563eb, #38bdf8); }

        .score-team-name {
            font-size: 18px;
            font-weight: 900;
            color: #111827;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .score-point {
            font-size: clamp(42px, 6vw, 62px);
            font-weight: 950;
            line-height: 1;
            color: #0f172a;
            font-variant-numeric: tabular-nums;
        }

        .score-unit {
            font-size: 16px;
            font-weight: 900;
            margin-left: 4px;
            color: #475569;
        }

        .score-vs {
            border-radius: 26px;
            background: rgba(255,255,255,.78);
            border: 1px solid rgba(255,255,255,.88);
            box-shadow: 0 14px 32px rgba(15, 23, 42, .08);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 12px 8px;
            backdrop-filter: blur(14px);
        }

        .score-vs-main {
            width: 58px;
            height: 58px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0f172a;
            color: #fff;
            font-size: 18px;
            font-weight: 950;
            letter-spacing: .06em;
            box-shadow: 0 12px 28px rgba(15, 23, 42, .20);
        }

        .score-status {
            font-size: 12px;
            font-weight: 850;
            color: #475569;
            margin-top: 9px;
            line-height: 1.35;
        }

        .share-card {
            border-radius: 22px;
            padding: 16px 18px;
            margin: 0 0 18px 0;
            background: rgba(255,255,255,.78);
            border: 1px solid rgba(255,255,255,.9);
            box-shadow: 0 12px 30px rgba(15, 23, 42, .08);
            backdrop-filter: blur(14px);
        }

        .share-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #475569;
            font-size: 12px;
            font-weight: 900;
            margin-bottom: 10px;
        }

        .share-track {
            display: flex;
            overflow: hidden;
            height: 16px;
            border-radius: 999px;
            background: #e2e8f0;
        }

        .share-red { background: linear-gradient(90deg, #ef4444, #fb7185); }
        .share-blue { background: linear-gradient(90deg, #2563eb, #38bdf8); }

        .insight-grid {
            display: grid;
            grid-template-columns: 1.25fr 1fr 1fr;
            gap: 14px;
            margin: 6px 0 20px 0;
        }

        .insight-card {
            position: relative;
            overflow: hidden;
            border-radius: 26px;
            padding: 20px 20px;
            background: rgba(255,255,255,.86);
            border: 1px solid rgba(255,255,255,.92);
            box-shadow: 0 14px 34px rgba(15, 23, 42, .09);
            backdrop-filter: blur(14px);
        }

        .insight-card::after {
            content: "";
            position: absolute;
            right: -42px;
            bottom: -46px;
            width: 128px;
            height: 128px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(37,99,235,.12), transparent 68%);
        }

        .insight-main::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 7px;
            background: linear-gradient(180deg, #ef4444, #2563eb);
        }

        .insight-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 10px;
        }

        .insight-title {
            color: #64748b;
            font-size: 12px;
            font-weight: 950;
            letter-spacing: .08em;
        }

        .insight-icon {
            width: 34px;
            height: 34px;
            border-radius: 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #f1f5f9;
            font-size: 18px;
        }

        .insight-value {
            color: #0f172a;
            font-size: 30px;
            font-weight: 950;
            line-height: 1.05;
            font-variant-numeric: tabular-nums;
        }

        .insight-main .insight-value {
            font-size: 34px;
        }

        .insight-note {
            color: #94a3b8;
            font-size: 12px;
            margin-top: 9px;
            font-weight: 800;
        }

        .insight-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }

        .insight-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            border-radius: 999px;
            padding: 6px 10px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475569;
            font-size: 11px;
            font-weight: 900;
        }

        .pill-red { color: #dc2626; background: #fff1f2; border-color: #fecdd3; }
        .pill-blue { color: #2563eb; background: #eff6ff; border-color: #bfdbfe; }

        .section-card {
            border-radius: 24px;
            padding: 18px 20px 16px 20px;
            margin: 18px 0 12px 0;
            background: rgba(255,255,255,.82);
            border: 1px solid rgba(255,255,255,.9);
            box-shadow: 0 12px 30px rgba(15, 23, 42, .08);
            backdrop-filter: blur(14px);
        }

        .section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 18px;
            font-weight: 950;
            color: #0f172a;
            margin-bottom: 4px;
        }

        .section-title span:first-child {
            width: 34px;
            height: 34px;
            border-radius: 13px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #f1f5f9;
        }

        .section-caption {
            color: #64748b;
            font-size: 13px;
            margin-left: 44px;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(226,232,240,.92);
            box-shadow: 0 10px 24px rgba(15, 23, 42, .055);
        }

        div[data-baseweb="select"] > div {
            border-radius: 16px;
            border-color: #dbe3ef;
            box-shadow: 0 7px 18px rgba(15, 23, 42, .06);
            background-color: rgba(255,255,255,.9);
        }

        .stButton > button,
        div[data-testid="stPageLink"] a {
            border-radius: 999px !important;
            font-weight: 900 !important;
            border: 1px solid rgba(15, 23, 42, .10) !important;
            box-shadow: 0 10px 22px rgba(15, 23, 42, .08) !important;
        }

        .empty-card {
            border-radius: 28px;
            padding: 42px 26px;
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, .15), transparent 35%),
                linear-gradient(135deg, rgba(255,255,255,.9), rgba(248,250,252,.9));
            border: 1px solid rgba(255,255,255,.9);
            text-align: center;
            box-shadow: 0 16px 42px rgba(15,23,42,.09);
            backdrop-filter: blur(14px);
        }

        .empty-title {
            font-size: 23px;
            font-weight: 950;
            color: #111827;
            margin-bottom: 8px;
        }

        .empty-text {
            color: #64748b;
            font-size: 14px;
        }

        .rank-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 0 0 18px 0;
        }

        .rank-card {
            display: flex;
            align-items: center;
            gap: 12px;
            border-radius: 22px;
            padding: 15px 15px;
            background: rgba(255,255,255,.82);
            border: 1px solid rgba(255,255,255,.9);
            box-shadow: 0 12px 30px rgba(15, 23, 42, .08);
            overflow: hidden;
            position: relative;
            backdrop-filter: blur(14px);
        }

        .rank-card::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 6px;
        }

        .rank-red::before { background: linear-gradient(180deg, #ef4444, #fb7185); }
        .rank-blue::before { background: linear-gradient(180deg, #2563eb, #38bdf8); }

        .rank-medal {
            width: 42px;
            height: 42px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8fafc;
            font-size: 22px;
            flex: 0 0 auto;
        }

        .rank-body { min-width: 0; flex: 1; }

        .rank-name {
            color: #111827;
            font-size: 15px;
            font-weight: 950;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .rank-meta {
            color: #64748b;
            font-size: 11px;
            font-weight: 800;
            margin-top: 3px;
        }

        .rank-point {
            color: #0f172a;
            font-size: 26px;
            font-weight: 950;
            flex: 0 0 auto;
            font-variant-numeric: tabular-nums;
        }

        .rank-point span {
            font-size: 11px;
            color: #64748b;
            margin-left: 2px;
        }

        .class-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 0 0 14px 0;
        }

        .class-card {
            border-radius: 22px;
            padding: 16px;
            background: rgba(255,255,255,.82);
            border: 1px solid rgba(255,255,255,.9);
            box-shadow: 0 12px 30px rgba(15, 23, 42, .08);
            backdrop-filter: blur(14px);
        }

        .class-name {
            font-size: 15px;
            color: #0f172a;
            font-weight: 950;
            margin-bottom: 12px;
        }

        .class-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 7px 0;
            border-top: 1px solid #eef2f7;
            color: #475569;
            font-size: 13px;
            font-weight: 850;
        }

        .class-row b {
            color: #0f172a;
            font-size: 18px;
            font-variant-numeric: tabular-nums;
        }

        @media (max-width: 900px) {
            /* スマホでもスコアボードは横並びを維持 */
            .score-board {
                grid-template-columns: minmax(0, 1fr) 74px minmax(0, 1fr);
                gap: 8px;
                align-items: stretch;
            }

            .score-card {
                border-radius: 22px;
                padding: 16px 10px 14px 10px;
                min-height: 142px;
            }

            .score-card::after {
                right: -54px;
                bottom: -56px;
                width: 126px;
                height: 126px;
            }

            .score-team-label {
                font-size: 9px;
                padding: 4px 9px;
                margin-bottom: 8px;
                letter-spacing: .06em;
            }

            .score-team-name {
                font-size: 14px;
                margin-bottom: 8px;
            }

            .score-point {
                font-size: 38px;
            }

            .score-unit {
                font-size: 12px;
            }

            .score-vs {
                min-height: 142px;
                border-radius: 22px;
                padding: 8px 5px;
            }

            .score-vs-main {
                width: 48px;
                height: 48px;
                font-size: 18px;
            }

            .score-status {
                font-size: 10px;
                line-height: 1.25;
                margin-top: 10px;
            }

            .insight-grid, .class-grid { grid-template-columns: 1fr; }
            .rank-grid { grid-template-columns: 1fr; }
        }

        @media (max-width: 560px) {
            .block-container {
                padding-left: .65rem;
                padding-right: .65rem;
            }

            .summary-hero {
                padding: 20px 16px;
                border-radius: 22px;
            }

            .summary-hero::after { display: none; }

            .score-board {
                grid-template-columns: minmax(0, 1fr) 58px minmax(0, 1fr);
                gap: 6px;
                margin-top: 10px;
            }

            .score-card {
                border-radius: 20px;
                padding: 14px 7px 12px 7px;
                min-height: 126px;
            }

            .score-card::before { height: 5px; }

            .score-team-label {
                font-size: 8px;
                padding: 4px 8px;
                margin-bottom: 7px;
            }

            .score-team-name {
                font-size: 13px;
            }

            .score-point {
                font-size: 34px;
            }

            .score-unit {
                font-size: 11px;
                margin-left: 1px;
            }

            .score-vs {
                min-height: 126px;
                border-radius: 20px;
                padding: 6px 3px;
            }

            .score-vs-main {
                width: 42px;
                height: 42px;
                font-size: 16px;
            }

            .score-status {
                font-size: 9px;
                margin-top: 8px;
                word-break: keep-all;
            }

            .insight-grid, .class-grid { grid-template-columns: 1fr; gap: 9px; }
            .section-caption { margin-left: 0; }
        }

        @media (max-width: 390px) {
            .score-board {
                grid-template-columns: minmax(0, 1fr) 50px minmax(0, 1fr);
                gap: 5px;
            }

            .score-card {
                min-height: 116px;
                padding-left: 5px;
                padding-right: 5px;
            }

            .score-team-label { font-size: 7px; padding: 3px 6px; }
            .score-team-name { font-size: 12px; }
            .score-point { font-size: 30px; }
            .score-vs { min-height: 116px; }
            .score-vs-main { width: 36px; height: 36px; font-size: 14px; }
            .score-status { font-size: 8px; }
        }
        </style>
        """,
    )


# =========================
# データ読み込み
# =========================
def load_scores():
    if not DATA_FILE.exists():
        return {}

    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"スコアデータの読み込みに失敗しました: {e}")
        return {}


def load_players():
    try:
        with sqlite3.connect(PLAYERS_DB_PATH) as conn:
            return pd.read_sql_query(
                """
                SELECT
                    uniform_number,
                    player_name,
                    team,
                    bibs_type,
                    class_type
                FROM players
                """,
                conn,
            )
    except Exception as e:
        st.warning(f"選手データの読み込みに失敗しました: {e}")
        return pd.DataFrame(
            columns=[
                "uniform_number",
                "player_name",
                "team",
                "bibs_type",
                "class_type",
            ]
        )


# =========================
# 集計関数
# =========================
def build_events(scores):
    rows = []

    for key, data in scores.items():
        try:
            team_code, score_no = key.split("_")
        except ValueError:
            continue

        mark = data.get("mark", "")
        point = POINT_MAP.get(mark, 0)

        if point <= 0:
            continue

        team_name = "Red" if team_code == "A" else "Blue"

        rows.append(
            {
                "TEAM": team_name,
                "列": team_code,
                "CLASS": data.get("class", ""),
                "背番号": str(data.get("number", "")).strip(),
                "スコア番号": int(score_no),
                "得点種別": mark,
                "得点": point,
            }
        )

    return pd.DataFrame(rows)


def attach_player_names(events_df, players_df):
    if events_df.empty:
        return events_df

    if players_df.empty:
        events_df = events_df.copy()
        events_df["名前"] = ""
        events_df["ビブスType"] = ""
        return events_df

    players_df = players_df.copy()
    players_df["uniform_number"] = players_df["uniform_number"].astype(str).str.strip()
    players_df["class_type"] = players_df["class_type"].astype(str).str.strip()
    players_df["team"] = players_df["team"].astype(str).str.strip()

    events_df = events_df.copy()
    events_df["背番号"] = events_df["背番号"].astype(str).str.strip()
    events_df["CLASS"] = events_df["CLASS"].astype(str).str.strip()
    events_df["TEAM"] = events_df["TEAM"].astype(str).str.strip()

    merged = events_df.merge(
        players_df,
        left_on=["背番号", "CLASS", "TEAM"],
        right_on=["uniform_number", "class_type", "team"],
        how="left",
    )

    merged.rename(
        columns={
            "player_name": "名前",
            "bibs_type": "ビブスType",
        },
        inplace=True,
    )

    if "名前" not in merged.columns:
        merged["名前"] = ""

    if "ビブスType" not in merged.columns:
        merged["ビブスType"] = ""

    merged["名前"] = merged["名前"].fillna("")
    merged["ビブスType"] = merged["ビブスType"].fillna("")

    return merged


def sort_class_team(df, columns):
    if df.empty:
        return df

    df = df.copy()
    if "CLASS" in df.columns:
        df["CLASS"] = pd.Categorical(df["CLASS"], categories=CLASS_ORDER, ordered=True)
    return df.sort_values(columns).reset_index(drop=True)


def calc_leader(red_total, blue_total):
    if red_total == blue_total:
        return "引き分け", ""
    if red_total > blue_total:
        return "Redがリード中", "red"
    return "Blueがリード中", "blue"


def section_header(icon, title, caption):
    render_html(
        f"""
        <div class="section-card">
            <div class="section-title"><span>{icon}</span><span>{title}</span></div>
            <div class="section-caption">{caption}</div>
        </div>
        """,
    )


def render_score_board(red_total, blue_total):
    status_text, winner = calc_leader(red_total, blue_total)
    red_winner = " winner" if winner == "red" else ""
    blue_winner = " winner" if winner == "blue" else ""

    render_html(
        f"""
        <div class="score-board">
            <div class="score-card red{red_winner}">
                <div class="score-team-label red-label">TEAM RED</div>
                <div class="score-team-name">Red</div>
                <div>
                    <span class="score-point">{red_total}</span>
                    <span class="score-unit">点</span>
                </div>
            </div>

            <div class="score-vs">
                <div class="score-vs-main">VS</div>
                <div class="score-status">{status_text}</div>
            </div>

            <div class="score-card blue{blue_winner}">
                <div class="score-team-label blue-label">TEAM BLUE</div>
                <div class="score-team-name">Blue</div>
                <div>
                    <span class="score-point">{blue_total}</span>
                    <span class="score-unit">点</span>
                </div>
            </div>
        </div>
        """,
    )


def render_team_share(red_total, blue_total):
    total = red_total + blue_total
    red_pct = round(red_total / total * 100, 1) if total else 0
    blue_pct = round(blue_total / total * 100, 1) if total else 0

    render_html(
        f"""
        <div class="share-card">
            <div class="share-head">
                <span>Red {red_pct}%</span>
                <span>得点シェア</span>
                <span>Blue {blue_pct}%</span>
            </div>
            <div class="share-track">
                <div class="share-red" style="width: {red_pct}%;"></div>
                <div class="share-blue" style="width: {blue_pct}%;"></div>
            </div>
        </div>
        """,
    )


def render_kpi_cards(events_df, player_summary, red_total, blue_total):
    total_points = red_total + blue_total
    total_events = len(events_df)
    active_players = len(player_summary)
    max_player_point = int(player_summary["得点"].max()) if not player_summary.empty else 0
    leader_text, winner = calc_leader(red_total, blue_total)
    lead_diff = abs(red_total - blue_total)
    avg_point = round(total_points / total_events, 1) if total_events else 0
    red_player_count = len(player_summary[player_summary["TEAM"] == "Red"]) if not player_summary.empty else 0
    blue_player_count = len(player_summary[player_summary["TEAM"] == "Blue"]) if not player_summary.empty else 0

    render_html(
        f"""
        <div class="insight-grid">
            <div class="insight-card insight-main">
                <div class="insight-top">
                    <div class="insight-title">MATCH STATUS</div>
                    <div class="insight-icon">🔥</div>
                </div>
                <div class="insight-value">{leader_text}</div>
                <div class="insight-note">点差 {lead_diff} 点 / 合計 {total_points} 点</div>
                <div class="insight-pills">
                    <span class="insight-pill pill-red">Red {red_total}点</span>
                    <span class="insight-pill pill-blue">Blue {blue_total}点</span>
                </div>
            </div>
            <div class="insight-card">
                <div class="insight-top">
                    <div class="insight-title">SCORING PACE</div>
                    <div class="insight-icon">⚡</div>
                </div>
                <div class="insight-value">{avg_point}<span style="font-size:13px;color:#64748b;margin-left:4px;">点/回</span></div>
                <div class="insight-note">得点イベント {total_events} 回</div>
                <div class="insight-pills"><span class="insight-pill">最高 {max_player_point}点</span></div>
            </div>
            <div class="insight-card">
                <div class="insight-top">
                    <div class="insight-title">ACTIVE PLAYERS</div>
                    <div class="insight-icon">👟</div>
                </div>
                <div class="insight-value">{active_players}<span style="font-size:13px;color:#64748b;margin-left:4px;">人</span></div>
                <div class="insight-note">得点した選手数</div>
                <div class="insight-pills">
                    <span class="insight-pill pill-red">Red {red_player_count}人</span>
                    <span class="insight-pill pill-blue">Blue {blue_player_count}人</span>
                </div>
            </div>
        </div>
        """,
    )

def score_column_config(df):
    """matplotlibを使わず、Streamlit標準機能だけで得点を見やすく表示する。"""
    if df is None or df.empty or "得点" not in df.columns:
        return {}

    max_score = int(df["得点"].max()) if int(df["得点"].max()) > 0 else 1

    return {
        "得点": st.column_config.ProgressColumn(
            "得点",
            help="得点が多いほどバーが長く表示されます",
            format="%d 点",
            min_value=0,
            max_value=max_score,
        )
    }


def render_table(df, height=None):
    """共通テーブル表示。height=Noneのときはheight引数を渡さない。"""
    kwargs = {
        "width": "stretch",
        "hide_index": True,
        "column_config": score_column_config(df),
    }
    if height is not None:
        kwargs["height"] = height

    st.dataframe(df, **kwargs)


def escape_html(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def render_top_players(player_summary):
    if player_summary.empty:
        return

    top_df = (
        player_summary.sort_values(["得点", "TEAM", "CLASS", "背番号"], ascending=[False, True, True, True])
        .head(3)
        .reset_index(drop=True)
    )

    cards = []
    medals = ["🥇", "🥈", "🥉"]
    for idx, row in top_df.iterrows():
        team_class = "rank-red" if row.get("TEAM") == "Red" else "rank-blue"
        name = escape_html(row.get("名前") or "名前未登録")
        uniform = escape_html(row.get("背番号", ""))
        class_type = escape_html(row.get("CLASS", ""))
        team = escape_html(row.get("TEAM", ""))
        point = int(row.get("得点", 0))
        cards.append(
            f"""
            <div class="rank-card {team_class}">
                <div class="rank-medal">{medals[idx]}</div>
                <div class="rank-body">
                    <div class="rank-name">{name}</div>
                    <div class="rank-meta">{team} / {class_type} / #{uniform}</div>
                </div>
                <div class="rank-point">{point}<span>点</span></div>
            </div>
            """
        )

    render_html(
        f"""
        <div class="rank-grid">
            {''.join(cards)}
        </div>
        """,
    )


def render_class_cards(class_summary):
    if class_summary.empty:
        return

    cards = []
    for class_name in CLASS_ORDER:
        class_df = class_summary[class_summary["CLASS"].astype(str) == class_name]
        red = int(class_df.loc[class_df["TEAM"] == "Red", "得点"].sum()) if not class_df.empty else 0
        blue = int(class_df.loc[class_df["TEAM"] == "Blue", "得点"].sum()) if not class_df.empty else 0
        cards.append(
            f"""
            <div class="class-card">
                <div class="class-name">{escape_html(class_name)}</div>
                <div class="class-row"><span>Red</span><b>{red}</b></div>
                <div class="class-row"><span>Blue</span><b>{blue}</b></div>
                <div class="class-row"><span>Total</span><b>{red + blue}</b></div>
            </div>
            """
        )

    render_html(
        f"""
        <div class="class-grid">
            {''.join(cards)}
        </div>
        """,
    )


# =========================
# 画面
# =========================
inject_style()

render_html(
    """
    <div class="summary-hero">
        <div class="hero-kicker">🏀 SCORE SUMMARY</div>
        <div class="hero-title">スコア集計</div>
        <div class="hero-subtitle">チーム別・CLASS別・選手別の得点状況をまとめて確認できます。</div>
    </div>
    """,
)

scores = load_scores()
players_df = load_players()

events_df = build_events(scores)
events_df = attach_player_names(events_df, players_df)

if events_df.empty:
    render_html(
        """
        <div class="empty-card">
            <div class="empty-title">まだ集計対象データがありません</div>
            <div class="empty-text">スコア入力画面で得点を登録すると、この画面に集計結果が表示されます。</div>
        </div>
        """,
    )

    st.divider()

    if hasattr(st, "page_link"):
        st.page_link("main.py", label="⬅️ main画面へ戻る", icon="🏠")
    else:
        if st.button("⬅️ main画面へ戻る"):
            st.switch_page("main.py")

    st.stop()


# =========================
# 合計スコア
# =========================
red_total = int(events_df.loc[events_df["TEAM"] == "Red", "得点"].sum())
blue_total = int(events_df.loc[events_df["TEAM"] == "Blue", "得点"].sum())

render_score_board(red_total, blue_total)
render_team_share(red_total, blue_total)


# =========================
# サマリ作成
# =========================
team_summary = (
    events_df.groupby("TEAM", as_index=False)["得点"]
    .sum()
    .sort_values("TEAM")
    .reset_index(drop=True)
)

class_summary = (
    events_df.groupby(["CLASS", "TEAM"], as_index=False)["得点"]
    .sum()
    .reset_index(drop=True)
)
class_summary = sort_class_team(class_summary, ["CLASS", "TEAM"])

player_summary = (
    events_df.groupby(
        ["TEAM", "CLASS", "背番号", "名前", "ビブスType"],
        as_index=False,
    )["得点"]
    .sum()
    .reset_index(drop=True)
)
player_summary = sort_class_team(player_summary, ["TEAM", "CLASS", "背番号"])


section_header("🏆", "得点ランキング TOP3", "得点上位の選手をカードで見やすく表示します。")
render_top_players(player_summary)


# =========================
# チーム別合計
# =========================
section_header("📌", "チーム別合計", "Red / Blue の総得点を比較します。")
render_table(team_summary)


# =========================
# CLASS別・チーム別得点
# =========================
section_header("🚀", "CLASS別・チーム別得点", "初級・中級・上級ごとの得点バランスを確認できます。")
render_class_cards(class_summary)
render_table(class_summary)


# =========================
# 選手別集計
# =========================
section_header("🏅", "選手別集計", "選手ごとの得点合計を確認します。得点王探しに便利です。")
render_table(player_summary, height=360)


# =========================
# CLASS × TEAM フィルター
# =========================
section_header("🔍", "CLASS × TEAM 絞り込み", "CLASSやTEAMを指定して、対象選手だけを絞り込めます。")

col_cls, col_team = st.columns(2)

with col_cls:
    class_options = ["すべて"] + sorted(events_df["CLASS"].dropna().unique().tolist())
    selected_class = st.selectbox("CLASS", class_options)

with col_team:
    team_options = ["すべて"] + sorted(events_df["TEAM"].dropna().unique().tolist())
    selected_team = st.selectbox("TEAM", team_options)

filtered_df = player_summary.copy()

if selected_class != "すべて":
    filtered_df = filtered_df[filtered_df["CLASS"] == selected_class]

if selected_team != "すべて":
    filtered_df = filtered_df[filtered_df["TEAM"] == selected_team]

render_table(filtered_df, height=320)

st.divider()

if hasattr(st, "page_link"):
    st.page_link("main.py", label="⬅️ main画面へ戻る", icon="🏠")
else:
    if st.button("⬅️ main画面へ戻る"):
        st.switch_page("main.py")
