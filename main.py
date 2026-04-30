import json
import html as html_lib
from pathlib import Path
from io import BytesIO
import sqlite3

import pandas as pd
import streamlit as st
from st_click_detector import click_detector

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from app_auth import require_login, render_userbox


# =========================
# ページ設定・認証
# =========================
st.set_page_config(page_title="スコアシート入力", page_icon="🏀", layout="wide")
st.session_state["login_redirect_to"] = "main.py"
require_login()
# render_userbox は他の共通処理・ページ側で呼ばれている場合に
# DuplicateElementKey になるため、main.py では呼ばない。


# =========================
# 定数
# =========================
DATA_FILE = Path("score_sheet_data.json")
PLAYERS_DB_PATH = "players.db"

DISPLAY_MARK_MAP = {
    "1点": "●",
    "2点": "／",
    "3点": "／",
}

POINT_MAP = {"": 0, "1点": 1, "2点": 2, "3点": 3}
CLASS_OPTIONS = ["初級", "中級", "上級"]


# =========================
# 画面デザイン
# =========================
def inject_global_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;800;900&display=swap');

        :root {
            --bg-a: #fff7ed;
            --bg-b: #f8fafc;
            --bg-c: #eef2ff;
            --ink: #0f172a;
            --muted: #64748b;
            --glass: rgba(255, 255, 255, 0.78);
            --orange: #f97316;
            --orange-dark: #ea580c;
            --shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
            --shadow-soft: 0 14px 34px rgba(15, 23, 42, 0.08);
        }

        html, body, [class*="css"] {
            font-family: 'Noto Sans JP', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 6% 4%, rgba(249, 115, 22, 0.25), transparent 28rem),
                radial-gradient(circle at 92% 10%, rgba(37, 99, 235, 0.18), transparent 30rem),
                linear-gradient(135deg, var(--bg-a) 0%, var(--bg-b) 52%, var(--bg-c) 100%);
            color: var(--ink);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }

        [data-testid="stHeader"] {
            background: rgba(255,255,255,0);
        }

        .app-hero {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 22px;
            align-items: center;
            padding: 26px 28px;
            margin-bottom: 18px;
            border: 1px solid rgba(255,255,255,.65);
            border-radius: 34px;
            background:
                linear-gradient(135deg, rgba(255,255,255,.92), rgba(255,247,237,.80)),
                radial-gradient(circle at top right, rgba(249,115,22,.30), transparent 18rem);
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 13px;
            border-radius: 999px;
            background: linear-gradient(135deg, #ffedd5, #fed7aa);
            color: #9a3412;
            font-weight: 900;
            font-size: 12px;
            letter-spacing: .08em;
            margin-bottom: 12px;
        }

        .hero-title {
            font-size: clamp(32px, 4.2vw, 54px);
            font-weight: 950;
            letter-spacing: -0.07em;
            line-height: .98;
            margin: 0;
            color: #0f172a;
        }

        .hero-caption {
            color: var(--muted);
            font-size: 15px;
            font-weight: 700;
            margin-top: 12px;
        }

        .hero-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 16px;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 9px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,.74);
            border: 1px solid rgba(15,23,42,.08);
            color: #334155;
            font-size: 12px;
            font-weight: 850;
        }

        .hero-ball-wrap {
            width: 112px;
            height: 112px;
            border-radius: 32px;
            display: grid;
            place-items: center;
            background: radial-gradient(circle at 30% 24%, #fdba74, #fb923c 42%, #ea580c 78%);
            box-shadow: 0 22px 46px rgba(234, 88, 12, .30);
            color: white;
            font-size: 58px;
            transform: rotate(-4deg);
        }

        .glass-panel {
            border: 1px solid rgba(255,255,255,.70);
            border-radius: 28px;
            background: var(--glass);
            box-shadow: var(--shadow-soft);
            padding: 18px;
            margin: 14px 0;
            backdrop-filter: blur(16px);
        }

        .section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 17px;
            font-weight: 950;
            margin: 4px 0 12px;
            color: #0f172a;
        }

        .hint-card {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255,255,255,.86), rgba(255,237,213,.78));
            border: 1px solid rgba(249, 115, 22, 0.20);
            color: #9a3412;
            font-weight: 850;
            margin: 14px 0 16px;
            box-shadow: 0 12px 28px rgba(249,115,22,.08);
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stSelectbox"] label,
        div[data-testid="stRadio"] label {
            font-weight: 900;
            color: var(--ink);
        }

        div[data-testid="stTextInput"] input {
            border-radius: 18px;
            border: 1px solid rgba(15,23,42,.12);
            background: rgba(255,255,255,.94);
            box-shadow: 0 10px 22px rgba(15,23,42,.05);
            min-height: 46px;
            font-weight: 750;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 18px !important;
            border: 1px solid rgba(15,23,42,.10) !important;
            box-shadow: 0 12px 26px rgba(15,23,42,.10);
            font-weight: 900 !important;
            min-height: 44px;
        }

        .stDownloadButton > button {
            background: linear-gradient(135deg, #fb923c, #ea580c) !important;
            color: white !important;
            border: none !important;
        }

        hr {
            border-color: rgba(15,23,42,.08) !important;
            margin: 1.8rem 0 !important;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-top: 138px !important;
                padding-left: .55rem !important;
                padding-right: .55rem !important;
            }

            .score-board {
                position: fixed !important;
                top: 28px !important;
                left: 8px !important;
                right: 8px !important;
                z-index: 99999 !important;

                display: grid !important;
                grid-template-columns: minmax(0, 1fr) 42px minmax(0, 1fr) !important;
                gap: 6px !important;

                margin: 0 !important;
                padding: 6px !important;
                border-radius: 22px !important;
                background: rgba(255,255,255,.94) !important;
                backdrop-filter: blur(16px) !important;
                box-shadow: 0 12px 28px rgba(15,23,42,.18) !important;
            }

            .score-card {
                min-height: 78px !important;
                padding: 8px 5px !important;
                border-radius: 18px !important;
                box-shadow: none !important;
            }

            .team-badge {
                min-width: 52px !important;
                padding: 3px 7px !important;
                font-size: 9px !important;
                margin-bottom: 4px !important;
            }

            .score-team-name {
                font-size: 12px !important;
                line-height: 1.1 !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }

            .score-point {
                font-size: 32px !important;
                line-height: .95 !important;
            }

            .score-unit {
                font-size: 10px !important;
                margin-left: 2px !important;
            }

            .versus-card {
                width: 42px !important;
                min-width: 42px !important;
                min-height: 78px !important;
                padding: 6px 3px !important;
                border-radius: 17px !important;
                box-shadow: none !important;
            }

            .versus-main {
                font-size: 14px !important;
            }

            .versus-sub {
                display: none !important;
            }

            .hint-card {
                margin-top: 12px !important;
            }
        }
        
        /* ダイアログ右上の×ボタンを非表示 */
        button[aria-label="Close"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# PDFフォント
# =========================
try:
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    PDF_FONT = "HeiseiKakuGo-W5"
except Exception:
    PDF_FONT = "Helvetica"


# =========================
# 共通関数
# =========================
def to_circle_number(num_str):
    circle_map = {
        "1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤",
        "6": "⑥", "7": "⑦", "8": "⑧", "9": "⑨", "10": "⑩",
        "11": "⑪", "12": "⑫", "13": "⑬", "14": "⑭", "15": "⑮",
        "16": "⑯", "17": "⑰", "18": "⑱", "19": "⑲", "20": "⑳",
        "21": "㉑", "22": "㉒", "23": "㉓", "24": "㉔", "25": "㉕",
        "26": "㉖", "27": "㉗", "28": "㉘", "29": "㉙", "30": "㉚",
        "31": "㉛", "32": "㉜", "33": "㉝", "34": "㉞", "35": "㉟",
        "36": "㊱", "37": "㊲", "38": "㊳", "39": "㊴", "40": "㊵",
    }
    return circle_map.get(str(num_str).strip(), str(num_str).strip())


def remove_cell_query_param():
    try:
        st.query_params.pop("cell", None)
    except Exception:
        pass


def fetch_players():
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
                ORDER BY team, class_type, uniform_number
                """,
                conn,
            )
    except Exception as e:
        st.warning(f"選手DBを読み込めませんでした: {e}")
        return pd.DataFrame(
            columns=["uniform_number", "player_name", "team", "bibs_type", "class_type"]
        )


def default_scores():
    scores = {}
    for score_no in range(1, 161):
        for team in ["A", "B"]:
            scores[f"{team}_{score_no}"] = {
                "mark": "",
                "class": "初級",
                "number": "",
            }
    return scores


def load_scores():
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            scores = default_scores()
            scores.update(data)
            return scores
        except Exception:
            return default_scores()
    return default_scores()


def save_scores():
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(st.session_state.scores, f, ensure_ascii=False, indent=2)


def init_state():
    if "scores" not in st.session_state:
        st.session_state.scores = load_scores()
    if "selected_cell" not in st.session_state:
        st.session_state.selected_cell = ""
    if "show_score_dialog" not in st.session_state:
        st.session_state.show_score_dialog = False
    if "dialog_cell" not in st.session_state:
        st.session_state.dialog_cell = ""
    if "click_nonce" not in st.session_state:
        st.session_state.click_nonce = 0
    if "last_selected_class" not in st.session_state:
        st.session_state.last_selected_class = "初級"
    if "last_clicked_cell" not in st.session_state:
        st.session_state.last_clicked_cell = ""

def open_score_dialog(cell_key: str):
    st.session_state.selected_cell = cell_key
    st.session_state.dialog_cell = cell_key
    st.session_state.show_score_dialog = True


def close_score_dialog():
    st.session_state.show_score_dialog = False
    st.session_state.dialog_cell = ""
    st.session_state.last_clicked_cell = ""
    st.session_state.click_nonce += 1


# =========================
# 画面用 ランニングスコアHTML
# =========================
def make_running_score_html(selected_cell="", start_block=0, end_block=4):
    html = ""

    html += "<style>"
    html += ".score-wrap { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; padding: 18px; border-radius: 30px; background: rgba(255,255,255,.76); border: 1px solid rgba(255,255,255,.78); box-shadow: 0 22px 60px rgba(15,23,42,.12); backdrop-filter: blur(16px); }"
    html += ".score-title-main { text-align: center; font-size: 15px; font-weight: 950; letter-spacing: .12em; padding: 13px; border: 1px solid rgba(255,255,255,.18); border-radius: 20px; background: linear-gradient(135deg, #0f172a, #1e293b 48%, #334155); color: white; margin-bottom: 14px; box-shadow: 0 14px 28px rgba(15,23,42,.20); }"
    html += ".score-block-row { display: flex; gap: 12px; align-items: flex-start; justify-content: center; }"
    html += ".score-block-table { border-collapse: separate; border-spacing: 0; font-family: 'Noto Sans JP', Inter, Arial, sans-serif; font-size: 13px; text-align: center; background: white; color: #0f172a; border: 1px solid rgba(15,23,42,.12); border-radius: 18px; overflow: hidden; box-shadow: 0 14px 32px rgba(15,23,42,.08); }"
    html += ".score-block-table th, .score-block-table td { border-right: 1px solid rgba(15,23,42,.12); border-bottom: 1px solid rgba(15,23,42,.12); width: 46px; height: 32px; padding: 0; }"
    html += ".score-block-table tr:last-child td { border-bottom: 0; }"
    html += ".score-block-table th:last-child, .score-block-table td:last-child { border-right: 0; }"
    html += ".score-block-table th { background: linear-gradient(135deg, #f8fafc, #e2e8f0); font-size: 12px; font-weight: 950; color: #0f172a; }"
    html += ".input-cell { background: linear-gradient(135deg, #f8fafc, #e2e8f0); cursor: pointer; font-weight: 950; font-size: 18px; transition: transform .14s ease, box-shadow .14s ease, filter .14s ease; }"
    html += ".input-cell:hover { transform: scale(1.045); filter: brightness(1.02); box-shadow: inset 0 0 0 2px rgba(249,115,22,.62); }"
    html += ".input-cell a { display: block; width: 100%; height: 100%; color: inherit; text-decoration: none; line-height: 32px; }"
    html += ".selected-cell { background: linear-gradient(135deg, #fed7aa, #fb923c) !important; outline: 3px solid #ea580c; outline-offset: -3px; }"
    html += ".cell-one { background: linear-gradient(135deg, #dcfce7, #bbf7d0) !important; }"
    html += ".cell-two { background: linear-gradient(135deg, #dbeafe, #bfdbfe) !important; }"
    html += ".cell-three { background: linear-gradient(135deg, #fee2e2, #fecaca) !important; }"
    html += ".score-no { background: #ffffff; color: #334155; font-size: 12px; font-weight: 850; position: relative; }"
    html += ".score-mark { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); font-size: 22px; font-weight: 950; color: #0f172a; pointer-events: none; }"
    html += ".class-beginner { color: #dc2626 !important; }"
    html += ".class-intermediate { color: #2563eb !important; }"
    html += ".class-advanced { color: #111827 !important; }"
    html += "@media (max-width: 768px) {"
    html += ".score-wrap { overflow-x: hidden; padding: 12px; border-radius: 22px; }"
    html += ".score-block-row { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }"
    html += ".score-block-table { width: calc(50% - 6px); font-size: 11px; border-radius: 15px; }"
    html += ".score-block-table th, .score-block-table td { width: 34px; height: 26px; }"
    html += ".input-cell { font-size: 14px; }"
    html += ".input-cell a { line-height: 26px; }"
    html += ".score-no { font-size: 10px; }"
    html += ".score-mark { top: -3px; font-size: 17px; }"
    html += ".score-title-main { font-size: 12px; padding: 9px; }"
    html += "}"
    html += "</style>"

    def cell_class(key, mark):
        classes = ["input-cell"]
        if key == selected_cell:
            classes.append("selected-cell")
        if mark == "1点":
            classes.append("cell-one")
        elif mark == "2点":
            classes.append("cell-two")
        elif mark == "3点":
            classes.append("cell-three")
        return " ".join(classes)

    def class_color_class(class_type):
        if class_type == "初級":
            return "class-beginner"
        elif class_type == "中級":
            return "class-intermediate"
        elif class_type == "上級":
            return "class-advanced"
        return ""

    html += '<div class="score-wrap">'
    html += '<div class="score-title-main">ランニングスコア　RUNNING SCORE</div>'
    html += '<div class="score-block-row">'

    for block in range(start_block, end_block):
        html += '<table class="score-block-table">'
        html += "<tr>"
        html += '<th colspan="2">A</th>'
        html += "<th colspan='2'>B</th>"
        html += "</tr>"

        for row in range(40):
            score_no = block * 40 + row + 1
            a_key = f"A_{score_no}"
            b_key = f"B_{score_no}"

            a_data = st.session_state.scores[a_key]
            b_data = st.session_state.scores[b_key]

            a_mark = a_data["mark"]
            b_mark = b_data["mark"]
            a_display_mark = DISPLAY_MARK_MAP.get(a_mark, "")
            b_display_mark = DISPLAY_MARK_MAP.get(b_mark, "")
            a_number = a_data["number"]
            b_number = b_data["number"]
            a_class_type = a_data["class"]
            b_class_type = b_data["class"]

            a_class = cell_class(a_key, a_mark)
            b_class = cell_class(b_key, b_mark)
            a_color_class = class_color_class(a_class_type)
            b_color_class = class_color_class(b_class_type)

            a_text = ""
            b_text = ""

            if a_mark:
                a_text = to_circle_number(a_number) if a_mark == "3点" else a_number

            if b_mark:
                b_text = to_circle_number(b_number) if b_mark == "3点" else b_number

            html += "<tr>"
            html += (
                f'<td class="{a_class} {a_color_class}">'
                f'<a href="#" id="{a_key}">{html_lib.escape(str(a_text))}</a>'
                f"</td>"
            )
            html += (
                f'<td class="score-no">{score_no}'
                f'<span class="score-mark">{a_display_mark}</span></td>'
            )
            html += (
                f'<td class="score-no">{score_no}'
                f'<span class="score-mark">{b_display_mark}</span></td>'
            )
            html += (
                f'<td class="{b_class} {b_color_class}">'
                f'<a href="#" id="{b_key}">{html_lib.escape(str(b_text))}</a>'
                f"</td>"
            )
            html += "</tr>"

        html += "</table>"

    html += "</div>"
    html += "</div>"

    return html


# =========================
# PDF作成
# =========================
def create_score_sheet_pdf(team_a_name, team_b_name):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_w, page_h = A4
    font = PDF_FONT

    template_path = Path(__file__).with_name("score_sheet_template.png")
    if not template_path.exists():
        template_path = Path("score_sheet_template.png")

    if not template_path.exists():
        raise FileNotFoundError(
            "score_sheet_template.png が見つかりません。"
            "このPythonファイルと同じフォルダに配置してください。"
        )

    bg = ImageReader(str(template_path))
    c.drawImage(bg, 0, 0, width=page_w, height=page_h, mask="auto")

    scores = getattr(st.session_state, "scores", None)
    if not scores:
        scores = load_scores()

    def set_font(size):
        c.setFont(font, size)

    def draw_text_center(x, y, value, size=6, color=colors.black):
        c.setFillColor(color)
        set_font(size)
        c.drawCentredString(x, y, "" if value is None else str(value))
        c.setFillColor(colors.black)

    def draw_text_left(x, y, value, size=6, color=colors.black):
        c.setFillColor(color)
        set_font(size)
        c.drawString(x, y, "" if value is None else str(value))
        c.setFillColor(colors.black)

    def player_color(class_type):
        if class_type == "初級":
            return colors.red
        if class_type == "中級":
            return colors.blue
        return colors.black

    def draw_score_mark(cx, cy, mark):
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)
        if mark == "1点":
            c.circle(cx, cy, 1.7, stroke=0, fill=1)
        elif mark in ("2点", "3点"):
            c.setLineWidth(0.9)
            c.line(cx - 3.2, cy - 2.8, cx + 3.2, cy + 3.8)

    def draw_player_number(cx, cy, number, mark, class_type):
        number = "" if number is None else str(number).strip()
        if not number:
            return
        if mark == "3点":
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.7)
            c.circle(cx, cy + 0.5, 4.5, stroke=1, fill=0)
            draw_text_center(cx, cy - 1.7, number, size=5.0, color=colors.black)
        else:
            draw_text_center(cx, cy - 2.0, number, size=6.0, color=player_color(class_type))

    c.setFillColor(colors.white)
    c.rect(58, page_h - 24, 160, 12, stroke=0, fill=1)
    c.rect(360, page_h - 24, 160, 12, stroke=0, fill=1)
    draw_text_left(60, page_h - 22, team_a_name, 7)
    draw_text_left(362, page_h - 22, team_b_name, 7)

    RUNNING_SCORE_LAYOUT = {
        "erase_x": 0,
        "erase_y": 0,
        "erase_w": 0,
        "erase_h": 0,
        "x": 309,
        "top_y": 750,
        "cell_w": 15.2,
        "cell_h": 12.35,
        "block_gap": 10.6,
    }

    lx = RUNNING_SCORE_LAYOUT["x"]
    top_y = RUNNING_SCORE_LAYOUT["top_y"]
    cell_w = RUNNING_SCORE_LAYOUT["cell_w"]
    cell_h = RUNNING_SCORE_LAYOUT["cell_h"]
    block_gap = RUNNING_SCORE_LAYOUT["block_gap"]
    block_w = cell_w * 4

    c.setFillColor(colors.white)
    c.rect(
        RUNNING_SCORE_LAYOUT["erase_x"],
        RUNNING_SCORE_LAYOUT["erase_y"],
        RUNNING_SCORE_LAYOUT["erase_w"],
        RUNNING_SCORE_LAYOUT["erase_h"],
        stroke=0,
        fill=1,
    )
    c.setFillColor(colors.black)

    draw_text_center(
        lx + (block_w * 4 + block_gap * 3) / 2,
        top_y + 8,
        "ランニングスコア  RUNNING SCORE",
        size=7,
    )

    c.setLineWidth(0.45)
    c.setStrokeColor(colors.black)

    for block in range(4):
        bx = lx + block * (block_w + block_gap)
        c.setFillColor(colors.white)
        c.rect(bx, top_y - cell_h, cell_w * 2, cell_h, stroke=1, fill=1)
        c.rect(bx + cell_w * 2, top_y - cell_h, cell_w * 2, cell_h, stroke=1, fill=1)
        draw_text_center(bx + cell_w, top_y - cell_h + 3.1, "A", size=5.5)
        draw_text_center(bx + cell_w * 3, top_y - cell_h + 3.1, "B", size=5.5)

        for row in range(40):
            score_no = block * 40 + row + 1
            y0 = top_y - cell_h * (row + 2)
            a_data = scores.get(f"A_{score_no}", {})
            b_data = scores.get(f"B_{score_no}", {})
            a_mark = a_data.get("mark", "")
            b_mark = b_data.get("mark", "")
            a_number = a_data.get("number", "")
            b_number = b_data.get("number", "")
            a_class = a_data.get("class", "")
            b_class = b_data.get("class", "")

            c.setFillColor(colors.lightgrey)
            c.rect(bx, y0, cell_w, cell_h, stroke=1, fill=1)
            draw_player_number(bx + cell_w / 2, y0 + cell_h / 2, a_number, a_mark, a_class)

            c.setFillColor(colors.white)
            c.rect(bx + cell_w, y0, cell_w, cell_h, stroke=1, fill=1)
            draw_text_center(bx + cell_w * 1.5, y0 + 2.8, score_no, size=5.2)
            draw_score_mark(bx + cell_w * 1.5, y0 + cell_h / 2, a_mark)

            c.setFillColor(colors.white)
            c.rect(bx + cell_w * 2, y0, cell_w, cell_h, stroke=1, fill=1)
            draw_text_center(bx + cell_w * 2.5, y0 + 2.8, score_no, size=5.2)
            draw_score_mark(bx + cell_w * 2.5, y0 + cell_h / 2, b_mark)

            c.setFillColor(colors.lightgrey)
            c.rect(bx + cell_w * 3, y0, cell_w, cell_h, stroke=1, fill=1)
            draw_player_number(bx + cell_w * 3.5, y0 + cell_h / 2, b_number, b_mark, b_class)

    events_df = build_events(team_a_name, team_b_name)
    a_total = get_team_total(events_df, team_a_name)
    b_total = get_team_total(events_df, team_b_name)
    draw_text_center(470, 76, str(a_total), size=12)
    draw_text_center(550, 76, str(b_total), size=12)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# =========================
# ダイアログ
# =========================
@st.dialog("スコア入力")
def score_dialog(cell_key: str):
    data = st.session_state.scores[cell_key]
    team, score_no = cell_key.split("_")

    st.markdown(f"### 🏀 スコア入力")
    st.caption(f"対象：{team} / スコア番号 {score_no}")

    mark_options = ["2点", "3点", "1点"]
    default_mark = data["mark"] if data["mark"] else "2点"

    mark = st.radio(
        "得点種別",
        mark_options,
        index=mark_options.index(default_mark),
        horizontal=True,
        key=f"mark_radio_{cell_key}",
    )

    default_class = st.session_state.get("last_selected_class", data.get("class", "初級"))

    if default_class not in CLASS_OPTIONS:
        default_class = "初級"

    player_class = st.radio(
        "CLASS",
        CLASS_OPTIONS,
        index=CLASS_OPTIONS.index(default_class),
        horizontal=True,
        key=f"class_radio_{cell_key}",
    )

    players_df = fetch_players()
    team_name_for_filter = "Red" if team == "A" else "Blue"
    filtered_players = players_df[players_df["team"] == team_name_for_filter].copy()
    filtered_players = filtered_players[filtered_players["class_type"] == player_class].copy()

    player_options = []
    player_numbers = []
    for _, row in filtered_players.iterrows():
        num = str(row["uniform_number"]).strip()
        label = f"{num} - {row['player_name']}"
        player_options.append(label)
        player_numbers.append(num)

    number = ""
    if player_options:
        current_number = str(data.get("number", "")).strip()
        default_index = player_numbers.index(current_number) if current_number in player_numbers else 0
        selected_player = st.selectbox(
            "選手選択",
            player_options,
            index=default_index,
            key=f"player_select_{cell_key}_{player_class}",
        )
        number = selected_player.split(" - ")[0]
    else:
        st.warning("該当する選手が登録されていません。")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("保存", type="primary", width="stretch", key=f"save_{cell_key}"):
            st.session_state.scores[cell_key] = {
                "mark": mark,
                "class": player_class,
                "number": number.strip(),
            }
            st.session_state["last_selected_class"] = player_class
            save_scores()
            st.session_state.selected_cell = cell_key
            close_score_dialog()
            st.rerun()

    with col2:
        if st.button("キャンセル", width="stretch", key=f"cancel_{cell_key}"):
            close_score_dialog()
            st.rerun()

    if st.button("このセルをクリア", width="stretch", key=f"clear_{cell_key}"):
        st.session_state.scores[cell_key] = {
            "mark": "",
            "class": "初級",
            "number": "",
        }
        save_scores()
        st.session_state.selected_cell = cell_key
        close_score_dialog()
        st.rerun()


# =========================
# 集計関数
# =========================
def build_events(team_a_name, team_b_name):
    rows = []
    for score_no in range(1, 161):
        for team in ["A", "B"]:
            key = f"{team}_{score_no}"
            data = st.session_state.scores[key]
            point = POINT_MAP.get(data["mark"], 0)
            if point <= 0:
                continue
            rows.append(
                {
                    "チーム": team_a_name if team == "A" else team_b_name,
                    "列": team,
                    "級": data["class"],
                    "背番号": data["number"],
                    "スコア番号": score_no,
                    "記号": data["mark"],
                    "得点": point,
                }
            )
    return pd.DataFrame(rows)


def build_summary(events_df):
    if events_df.empty:
        return pd.DataFrame(columns=["チーム", "級", "背番号", "得点"])
    return (
        events_df.groupby(["チーム", "級", "背番号"], as_index=False)["得点"]
        .sum()
        .sort_values(["チーム", "級", "背番号"])
        .reset_index(drop=True)
    )


def build_team_summary(events_df):
    if events_df.empty:
        return pd.DataFrame(columns=["チーム", "得点"])
    return (
        events_df.groupby("チーム", as_index=False)["得点"]
        .sum()
        .sort_values("チーム")
        .reset_index(drop=True)
    )


def get_team_total(events_df, team_name):
    if events_df.empty:
        return 0
    return int(events_df.loc[events_df["チーム"] == team_name, "得点"].sum())


# =========================
# 画面
# =========================
init_state()
inject_global_style()

st.markdown('<div class="app-shell">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="app-hero">
        <div>
            <div class="hero-eyebrow">🏀 LIVE SCORE SHEET</div>
            <h1 class="hero-title">スコアシート入力</h1>
            <div class="hero-caption">試合中の得点入力・集計・PDF出力を、1画面でスムーズに。</div>
            <div class="hero-actions">
                <span class="pill">⚡ リアルタイム集計</span>
                <span class="pill">🧾 PDF出力対応</span>
                <span class="pill">🎯 ランニングスコア入力</span>
            </div>
        </div>
        <div class="hero-ball-wrap">🏀</div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🏷️ チーム設定</div>', unsafe_allow_html=True)
team_col1, team_col2 = st.columns(2)
with team_col1:
    team_a_name = st.text_input("Aチーム名", value="Redチーム", key="team_a_name_input")
with team_col2:
    team_b_name = st.text_input("Bチーム名", value="Blueチーム", key="team_b_name_input")
st.markdown('</div>', unsafe_allow_html=True)

events_df = build_events(team_a_name, team_b_name)
summary_df = build_summary(events_df)
team_summary_df = build_team_summary(events_df)

a_total = get_team_total(events_df, team_a_name)
b_total = get_team_total(events_df, team_b_name)

# 上部スコアボード
a_team_safe = html_lib.escape(team_a_name)
b_team_safe = html_lib.escape(team_b_name)
lead_text = "同点です。次の1本が熱いです。" if a_total == b_total else f"{html_lib.escape(team_a_name if a_total > b_total else team_b_name)} がリード中"

st.markdown(
    f"""
    <style>
    .score-board {{
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        gap: 14px;
        align-items: stretch;
        margin: 14px 0 18px 0;
    }}
    .score-card {{
        position: relative;
        overflow: hidden;
        border-radius: 30px;
        padding: 22px 24px;
        background: rgba(255,255,255,.86);
        border: 1px solid rgba(255,255,255,.72);
        box-shadow: 0 24px 60px rgba(15,23,42,.12);
        text-align: center;
        min-height: 142px;
        backdrop-filter: blur(16px);
    }}
    .score-card::before {{
        content: "";
        position: absolute;
        inset: 0;
        opacity: .14;
        pointer-events: none;
    }}
    .score-card.red::before {{ background: radial-gradient(circle at top left, #ef4444, transparent 58%); }}
    .score-card.blue::before {{ background: radial-gradient(circle at top right, #2563eb, transparent 58%); }}
    .team-badge {{
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 88px;
        padding: 7px 13px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 950;
        letter-spacing: .10em;
        color: white;
        margin-bottom: 10px;
        box-shadow: 0 10px 20px rgba(15,23,42,.12);
    }}
    .score-card.red .team-badge {{ background: linear-gradient(135deg, #ef4444, #b91c1c); }}
    .score-card.blue .team-badge {{ background: linear-gradient(135deg, #3b82f6, #1d4ed8); }}
    .score-team-name {{
        position: relative;
        font-size: 21px;
        font-weight: 950;
        margin-bottom: 6px;
        color: #0f172a;
        letter-spacing: -.04em;
    }}
    .score-point {{
        position: relative;
        font-size: clamp(54px, 7.4vw, 84px);
        font-weight: 1000;
        line-height: .92;
        letter-spacing: -0.07em;
        color: #0f172a;
    }}
    .score-unit {{
        font-size: 16px;
        margin-left: 6px;
        color: #64748b;
        font-weight: 900;
    }}
    .versus-card {{
        min-width: 112px;
        border-radius: 28px;
        background: linear-gradient(135deg, #0f172a, #1e293b 48%, #334155);
        color: white;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 5px;
        box-shadow: 0 24px 60px rgba(15,23,42,.22);
        padding: 16px;
        text-align: center;
    }}
    .versus-main {{ font-size: 26px; font-weight: 1000; letter-spacing: .10em; }}
    .versus-sub {{ font-size: 12px; color: #cbd5e1; font-weight: 850; }}
    @media (max-width: 768px) {{
        .score-board {{ grid-template-columns: minmax(0, 1fr) 42px minmax(0, 1fr); gap: 6px; }}
        .score-card {{ min-height: 100px; padding: 12px 6px; border-radius: 20px; }}
        .team-badge {{ min-width: 58px; padding: 4px 8px; font-size: 10px; margin-bottom: 6px; }}
        .score-team-name {{ font-size: 13px; line-height: 1.15; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .score-point {{ font-size: 36px; }}
        .score-unit {{ font-size: 11px; margin-left: 2px; }}
        .versus-card {{ min-width: 0; width: 42px; min-height: 100px; padding: 8px 4px; border-radius: 18px; }}
        .versus-main {{ font-size: 16px; }}
        .versus-sub {{ display: none; }}
    }}
    </style>

    <div class="score-board">
        <div class="score-card red">
            <div class="team-badge">TEAM A</div>
            <div class="score-team-name">{a_team_safe}</div>
            <div><span class="score-point">{a_total}</span><span class="score-unit">点</span></div>
        </div>
        <div class="versus-card">
            <div class="versus-main">VS</div>
            <div class="versus-sub">{lead_text}</div>
        </div>
        <div class="score-card blue">
            <div class="team-badge">TEAM B</div>
            <div class="score-team-name">{b_team_safe}</div>
            <div><span class="score-point">{b_total}</span><span class="score-unit">点</span></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hint-card">💡 灰色セルをクリックすると入力画面が開きます。PDF出力前にチーム名と得点を確認してください。</div>',
    unsafe_allow_html=True,
)

score_range = st.radio(
    "表示範囲",
    ["🏀 1〜80点", "🔥 81〜160点"],
    horizontal=True,
    key="score_range_mode",
    label_visibility="collapsed",
)

if score_range == "🏀 1〜80点":
    start_block = 0
    end_block = 2
else:
    start_block = 2
    end_block = 4

clicked_cell = click_detector(
    make_running_score_html(
        st.session_state.selected_cell,
        start_block=start_block,
        end_block=end_block,
    ),
    key=f"score_click_{score_range}_{st.session_state.click_nonce}",
)

if (
    clicked_cell in st.session_state.scores
    and not st.session_state.show_score_dialog
):
    # クリックされたセルに応じて表示範囲も保持
    try:
        score_no = int(clicked_cell.split("_")[1])
        if score_no <= 80:
            st.session_state.score_range_mode = "🏀 1〜80点"
        else:
            st.session_state.score_range_mode = "🔥 81〜160点"
    except Exception:
        pass

    open_score_dialog(clicked_cell)

if st.session_state.show_score_dialog and st.session_state.dialog_cell:
    score_dialog(st.session_state.dialog_cell)

st.divider()

try:
    pdf_buffer = create_score_sheet_pdf(team_a_name, team_b_name)
    st.download_button(
        "📄 PDFをダウンロード",
        data=pdf_buffer,
        file_name="score_sheet.pdf",
        mime="application/pdf",
        width="stretch",
    )
except FileNotFoundError as e:
    st.warning(str(e))
except Exception as e:
    st.error(f"PDF作成に失敗しました: {e}")

st.divider()

if st.button("🧹 入力をすべてリセット", type="secondary"):
    st.session_state.scores = default_scores()
    st.session_state.selected_cell = ""
    save_scores()
    close_score_dialog()
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)