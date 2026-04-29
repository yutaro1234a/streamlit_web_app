import json
import html as html_lib
from pathlib import Path
from io import BytesIO
import sqlite3

import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from app_auth import require_login, render_userbox


# =========================
# ページ設定
# =========================
st.set_page_config(page_title="スコアシート入力", page_icon="🏀", layout="wide")

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

DISPLAY_MARK_MAP = {
    "1点": "●",
    "2点": "/",
    "3点": "/",
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
        :root {
            --app-bg-1: #fff7ed;
            --app-bg-2: #f8fafc;
            --card-bg: rgba(255, 255, 255, 0.88);
            --card-border: rgba(15, 23, 42, 0.08);
            --text-main: #0f172a;
            --text-sub: #64748b;
            --accent: #f97316;
            --accent-dark: #ea580c;
            --red: #ef4444;
            --blue: #2563eb;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(251, 146, 60, 0.24), transparent 34rem),
                radial-gradient(circle at top right, rgba(37, 99, 235, 0.14), transparent 30rem),
                linear-gradient(135deg, var(--app-bg-1) 0%, var(--app-bg-2) 52%, #eef2ff 100%);
            color: var(--text-main);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        [data-testid="stHeader"] {
            background: rgba(255,255,255,0);
        }

        .app-hero {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            padding: 22px 24px;
            margin-bottom: 18px;
            border: 1px solid var(--card-border);
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(255,255,255,.92), rgba(255,247,237,.82));
            box-shadow: 0 22px 50px rgba(15, 23, 42, 0.10);
            backdrop-filter: blur(14px);
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 999px;
            background: #ffedd5;
            color: #9a3412;
            font-weight: 800;
            font-size: 13px;
            margin-bottom: 10px;
        }

        .hero-title {
            font-size: clamp(30px, 4vw, 46px);
            font-weight: 950;
            letter-spacing: -0.05em;
            line-height: 1.02;
            margin: 0;
        }

        .hero-caption {
            color: var(--text-sub);
            font-size: 15px;
            margin-top: 10px;
        }

        .hero-ball {
            width: 92px;
            height: 92px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, #fb923c, #ea580c);
            color: white;
            font-size: 46px;
            box-shadow: 0 18px 36px rgba(234, 88, 12, .28);
            flex: 0 0 auto;
        }

        .glass-panel {
            border: 1px solid var(--card-border);
            border-radius: 24px;
            background: var(--card-bg);
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
            padding: 18px;
            margin: 14px 0;
        }

        .hint-card {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 14px;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid rgba(249, 115, 22, 0.18);
            color: #9a3412;
            font-weight: 700;
            margin: 12px 0 16px;
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stSelectbox"] label,
        div[data-testid="stRadio"] label {
            font-weight: 800;
            color: var(--text-main);
        }

        div[data-testid="stTextInput"] input {
            border-radius: 16px;
            border: 1px solid rgba(15,23,42,.12);
            background: rgba(255,255,255,.92);
            box-shadow: 0 8px 20px rgba(15,23,42,.05);
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 16px !important;
            border: 1px solid rgba(15,23,42,.10) !important;
            box-shadow: 0 10px 24px rgba(15,23,42,.08);
            font-weight: 850 !important;
        }

        .stDownloadButton > button {
            background: linear-gradient(135deg, #fb923c, #ea580c) !important;
            color: white !important;
            border: none !important;
        }

        hr {
            border-color: rgba(15,23,42,.08) !important;
            margin: 1.6rem 0 !important;
        }

        @media (max-width: 768px) {
            .block-container { padding: 1rem .75rem 2rem; }
            .app-hero { padding: 18px; border-radius: 22px; }
            .hero-ball { display: none; }
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
        # ①〜⑳
        "1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤",
        "6": "⑥", "7": "⑦", "8": "⑧", "9": "⑨", "10": "⑩",
        "11": "⑪", "12": "⑫", "13": "⑬", "14": "⑭", "15": "⑮",
        "16": "⑯", "17": "⑰", "18": "⑱", "19": "⑲", "20": "⑳",

        # ㉑〜㉟
        "21": "㉑", "22": "㉒", "23": "㉓", "24": "㉔", "25": "㉕",
        "26": "㉖", "27": "㉗", "28": "㉘", "29": "㉙", "30": "㉚",
        "31": "㉛", "32": "㉜", "33": "㉝", "34": "㉞", "35": "㉟",

        # ㊱〜㊵
        "36": "㊱", "37": "㊲", "38": "㊳", "39": "㊴", "40": "㊵",
    }
    return circle_map.get(str(num_str).strip(), str(num_str).strip())


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
    except Exception:
        return pd.DataFrame(
            columns=[
                "uniform_number",
                "player_name",
                "team",
                "bibs_type",
                "class_type",
            ]
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


def get_query_cell():
    cell = st.query_params.get("cell")

    if isinstance(cell, list):
        cell = cell[0] if cell else None

    if cell in st.session_state.scores:
        st.session_state.selected_cell = cell
        return cell

    return None


# =========================
# 画面用 ランニングスコアHTML
# =========================
def make_running_score_html(selected_cell=""):
    html = ""

    html += "<style>"
    html += ".score-wrap { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; padding: 18px; border-radius: 26px; background: rgba(255,255,255,.78); border: 1px solid rgba(15,23,42,.08); box-shadow: 0 18px 42px rgba(15,23,42,.08); }"
    html += ".score-title-main { text-align: center; font-size: 15px; font-weight: 900; letter-spacing: .08em; padding: 12px; border: 1px solid rgba(15,23,42,.08); border-radius: 18px; background: linear-gradient(135deg, #0f172a, #334155); color: white; margin-bottom: 14px; box-shadow: 0 10px 24px rgba(15,23,42,.16); }"

    html += ".score-block-row { display: flex; gap: 12px; align-items: flex-start; justify-content: center; }"
    html += ".score-block-table { border-collapse: separate; border-spacing: 0; font-family: Inter, 'Noto Sans JP', Arial, sans-serif; font-size: 13px; text-align: center; background: white; color: #0f172a; border: 1px solid rgba(15,23,42,.12); border-radius: 16px; overflow: hidden; box-shadow: 0 10px 24px rgba(15,23,42,.06); }"
    html += ".score-block-table th, .score-block-table td { border-right: 1px solid rgba(15,23,42,.12); border-bottom: 1px solid rgba(15,23,42,.12); width: 46px; height: 32px; padding: 0; }"
    html += ".score-block-table tr:last-child td { border-bottom: 0; }"
    html += ".score-block-table th:last-child, .score-block-table td:last-child { border-right: 0; }"
    html += ".score-block-table th { background: linear-gradient(135deg, #f8fafc, #e2e8f0); font-size: 12px; font-weight: 950; }"

    html += ".input-cell { background: linear-gradient(135deg, #f1f5f9, #e2e8f0); cursor: pointer; font-weight: 950; font-size: 18px; transition: transform .12s ease, box-shadow .12s ease, filter .12s ease; }"
    html += ".input-cell:hover { transform: scale(1.04); filter: brightness(1.02); box-shadow: inset 0 0 0 2px rgba(249,115,22,.55); }"
    html += ".input-cell a { display: block; width: 100%; height: 100%; color: inherit; text-decoration: none; line-height: 32px; }"
    html += ".selected-cell { background: linear-gradient(135deg, #fed7aa, #fdba74) !important; outline: 3px solid #f97316; outline-offset: -3px; }"

    html += ".cell-one { background: linear-gradient(135deg, #dcfce7, #bbf7d0) !important; }"
    html += ".cell-two { background: linear-gradient(135deg, #dbeafe, #bfdbfe) !important; }"
    html += ".cell-three { background: linear-gradient(135deg, #fee2e2, #fecaca) !important; }"

    html += ".score-no { background: #ffffff; color: #334155; font-size: 12px; font-weight: 750; position: relative; }"
    html += ".score-mark { position: absolute; top: -2px; left: 50%; transform: translateX(-50%); font-size: 22px; font-weight: 950; color: #0f172a; pointer-events: none; }"

    html += ".class-beginner { color: #dc2626 !important; }"
    html += ".class-intermediate { color: #2563eb !important; }"
    html += ".class-advanced { color: #111827 !important; }"

    # スマホ：2ブロック × 2段
    html += "@media (max-width: 768px) {"
    html += ".score-wrap { overflow-x: hidden; padding: 12px; border-radius: 20px; }"
    html += ".score-block-row { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }"
    html += ".score-block-table { width: calc(50% - 6px); font-size: 11px; border-radius: 14px; }"
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

    for block in range(4):
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
                if a_mark == "3点":
                    a_text = to_circle_number(a_number)
                else:
                    a_text = a_number

            if b_mark:
                if b_mark == "3点":
                    b_text = to_circle_number(b_number)
                else:
                    b_text = b_number

            html += "<tr>"

            html += (
                f'<td class="{a_class} {a_color_class}">'
                f'<a href="?cell={a_key}" target="_self">{html_lib.escape(str(a_text))}</a>'
                f"</td>"
            )

            html += (
                f'<td class="score-no">'
                f'{score_no}'
                f'<span class="score-mark">{a_display_mark}</span>'
                f'</td>'
            )

            html += (
                f'<td class="score-no">'
                f'{score_no}'
                f'<span class="score-mark">{b_display_mark}</span>'
                f'</td>'
            )

            html += (
                f'<td class="{b_class} {b_color_class}">'
                f'<a href="?cell={b_key}" target="_self">{html_lib.escape(str(b_text))}</a>'
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
    """
    PDFは「静的なスコアシート画像」を背景にし、
    ズレが目立ちやすいランニングスコア部分だけを白塗りして
    JSON / session_state のスコアから再描画する方式。

    重要:
    - score_sheet_template.png をこの .py と同じフォルダに置いてください。
    - ランニングスコア位置を微調整したい場合は RUNNING_SCORE_LAYOUT の値だけ変更します。
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_w, page_h = A4
    font = PDF_FONT

    # =========================
    # 背景テンプレート
    # =========================
    template_path = Path(__file__).with_name("score_sheet_template.png")
    if not template_path.exists():
        # Streamlit Cloud等で __file__ 基準が使いづらい場合の予備
        template_path = Path("score_sheet_template.png")

    if not template_path.exists():
        raise FileNotFoundError(
            "score_sheet_template.png が見つかりません。"
            "このPythonファイルと同じフォルダに配置してください。"
        )

    bg = ImageReader(str(template_path))
    c.drawImage(bg, 0, 0, width=page_w, height=page_h, mask="auto")

    # PDF出力時点の最新データを使う。
    # 通常は session_state、なければ JSON ファイルから読む。
    scores = getattr(st.session_state, "scores", None)
    if not scores:
        scores = load_scores()

    # =========================
    # 共通描画
    # =========================
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

    # =========================
    # ヘッダーのチーム名だけ上書き
    # =========================
    # 背景の罫線を消さないように、文字の周囲だけ白くする
    c.setFillColor(colors.white)
    c.rect(58, page_h - 24, 160, 12, stroke=0, fill=1)
    c.rect(360, page_h - 24, 160, 12, stroke=0, fill=1)
    draw_text_left(60, page_h - 22, team_a_name, 7)
    draw_text_left(362, page_h - 22, team_b_name, 7)

    # =========================
    # ランニングスコア部分だけ作り直し
    # =========================
    # A4上の座標。ここだけ調整すれば全体を触らずに位置合わせできます。
    RUNNING_SCORE_LAYOUT = {
        # =====================================================
        # ランニングスコア位置調整用
        # PDF座標は「左下が原点」です。
        #
        # 添付画像の右側空白エリアに、ランニングスコア表が
        # ぴったり収まるように再調整済みです。
        #
        # 位置を変えたい場合:
        #   x      : 数値を大きくすると右へ移動
        #   top_y  : 数値を大きくすると上へ移動
        #
        # 長さを変えたい場合:
        #   cell_h : 数値を大きくすると縦に長くなる
        #
        # 横幅を変えたい場合:
        #   cell_w    : 各マスの横幅
        #   block_gap : 40点ごとの表の間隔
        # =====================================================

        # 古いランニングスコア部分を消す白塗り範囲
        # 右側の大きな空白欄だけを消し、下のスコア欄にはかからない範囲
        # 古いランニングスコア部分を消す白塗り範囲
        "erase_x": 0,
        "erase_y": 0,
        "erase_w": 0,
        "erase_h": 0,

        # 新しく描くランニングスコア表
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

    # 既存のランニングスコアだけ消す
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

    # タイトル
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

        # ヘッダー
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

            # A 選手番号欄
            c.setFillColor(colors.lightgrey)
            c.rect(bx, y0, cell_w, cell_h, stroke=1, fill=1)
            draw_player_number(bx + cell_w / 2, y0 + cell_h / 2, a_number, a_mark, a_class)

            # A スコア番号欄
            c.setFillColor(colors.white)
            c.rect(bx + cell_w, y0, cell_w, cell_h, stroke=1, fill=1)
            draw_text_center(bx + cell_w * 1.5, y0 + 2.8, score_no, size=5.2)
            draw_score_mark(bx + cell_w * 1.5, y0 + cell_h / 2, a_mark)

            # B スコア番号欄
            c.setFillColor(colors.white)
            c.rect(bx + cell_w * 2, y0, cell_w, cell_h, stroke=1, fill=1)
            draw_text_center(bx + cell_w * 2.5, y0 + 2.8, score_no, size=5.2)
            draw_score_mark(bx + cell_w * 2.5, y0 + cell_h / 2, b_mark)

            # B 選手番号欄
            c.setFillColor(colors.lightgrey)
            c.rect(bx + cell_w * 3, y0, cell_w, cell_h, stroke=1, fill=1)
            draw_player_number(bx + cell_w * 3.5, y0 + cell_h / 2, b_number, b_mark, b_class)

    # =========================
    # 最終スコア欄も数字だけ上書き
    # =========================
    events_df = build_events(team_a_name, team_b_name)
    a_total = get_team_total(events_df, team_a_name)
    b_total = get_team_total(events_df, team_b_name)

    # 最終スコア A / B
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

    st.write(f"対象：{team} / スコア番号 {score_no}")

    mark_options = ["2点", "3点", "1点"]
    default_mark = data["mark"] if data["mark"] else "2点"

    mark = st.radio(
        "得点種別",
        mark_options,
        index=mark_options.index(default_mark),
        horizontal=True,
        key=f"mark_radio_{cell_key}",
    )

    player_class = st.selectbox(
        "CLASS",
        CLASS_OPTIONS,
        index=CLASS_OPTIONS.index(data["class"]),
        key=f"class_select_{cell_key}",
    )

    players_df = fetch_players()
    team_name_for_filter = "Red" if team == "A" else "Blue"

    filtered_players = players_df[players_df["team"] == team_name_for_filter].copy()
    filtered_players = filtered_players[filtered_players["class_type"] == player_class].copy()

    player_options = []

    for _, row in filtered_players.iterrows():
        label = f"{row['uniform_number']} - {row['player_name']}"
        player_options.append(label)

    if player_options:
        selected_player = st.selectbox(
            "選手選択",
            player_options,
            key=f"player_select_{cell_key}",
        )
        number = selected_player.split(" - ")[0]
    else:
        st.warning("該当する選手が登録されていません。")
        number = ""

    col1, col2 = st.columns(2)

    with col1:
        if st.button("保存", type="primary", width="stretch", key=f"save_{cell_key}"):
            st.session_state.scores[cell_key] = {
                "mark": mark,
                "class": player_class,
                "number": number.strip(),
            }
            save_scores()
            st.session_state.selected_cell = cell_key
            st.query_params.clear()
            st.rerun()

    with col2:
        if st.button("キャンセル", width="stretch", key=f"cancel_{cell_key}"):
            st.query_params.clear()
            st.rerun()

    if st.button("このセルをクリア", width="stretch", key=f"clear_{cell_key}"):
        st.session_state.scores[cell_key] = {
            "mark": "",
            "class": "初級",
            "number": "",
        }
        save_scores()
        st.session_state.selected_cell = cell_key
        st.query_params.clear()
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

st.markdown(
    """
    <div class="app-hero">
        <div>
            <div class="hero-eyebrow">🏀 LIVE SCORE SHEET</div>
            <h1 class="hero-title">スコアシート入力</h1>
            <div class="hero-caption"></div>
        </div>
        <div class="hero-ball">🏀</div>
    </div>
    """,
    unsafe_allow_html=True,
)

cell = get_query_cell()

team_col1, team_col2 = st.columns(2)

with team_col1:
    team_a_name = st.text_input("Aチーム名", value="Redチーム", key="team_a_name_input")

with team_col2:
    team_b_name = st.text_input("Bチーム名", value="Blueチーム", key="team_b_name_input")

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
        border-radius: 26px;
        padding: 20px 22px;
        background: rgba(255,255,255,.86);
        border: 1px solid rgba(15,23,42,.08);
        box-shadow: 0 18px 40px rgba(15,23,42,.09);
        text-align: center;
        min-height: 132px;
    }}
    .score-card::before {{
        content: "";
        position: absolute;
        inset: 0;
        opacity: .12;
        pointer-events: none;
    }}
    .score-card.red::before {{ background: radial-gradient(circle at top left, #ef4444, transparent 58%); }}
    .score-card.blue::before {{ background: radial-gradient(circle at top right, #2563eb, transparent 58%); }}
    .team-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 84px;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 950;
        letter-spacing: .08em;
        color: white;
        margin-bottom: 9px;
    }}
    .score-card.red .team-badge {{ background: linear-gradient(135deg, #ef4444, #b91c1c); }}
    .score-card.blue .team-badge {{ background: linear-gradient(135deg, #3b82f6, #1d4ed8); }}
    .score-team-name {{
        position: relative;
        font-size: 20px;
        font-weight: 900;
        margin-bottom: 4px;
        color: #0f172a;
    }}
    .score-point {{
        position: relative;
        font-size: clamp(48px, 7vw, 76px);
        font-weight: 1000;
        line-height: .95;
        letter-spacing: -0.06em;
        color: #0f172a;
    }}
    .score-unit {{
        font-size: 16px;
        margin-left: 6px;
        color: #64748b;
        font-weight: 850;
    }}
    .versus-card {{
        min-width: 104px;
        border-radius: 24px;
        background: linear-gradient(135deg, #0f172a, #334155);
        color: white;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 4px;
        box-shadow: 0 18px 40px rgba(15,23,42,.16);
        padding: 14px;
        text-align: center;
    }}
    .versus-main {{ font-size: 24px; font-weight: 1000; letter-spacing: .08em; }}
    .versus-sub {{ font-size: 12px; color: #cbd5e1; font-weight: 750; }}
    .lead-text {{
        margin-top: 10px;
        color: #64748b;
        font-weight: 800;
        font-size: 13px;
    }}
    @media (max-width: 768px) {{
        .score-board {{
            grid-template-columns: minmax(0, 1fr) 42px minmax(0, 1fr);
            gap: 6px;
            align-items: stretch;
        }}
        .score-card {{
            min-height: 96px;
            padding: 12px 6px;
            border-radius: 20px;
        }}
        .team-badge {{
            min-width: 58px;
            padding: 4px 8px;
            font-size: 10px;
            margin-bottom: 6px;
        }}
        .score-team-name {{
            font-size: 13px;
            line-height: 1.15;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .score-point {{
            font-size: 34px;
            letter-spacing: -0.06em;
        }}
        .score-unit {{
            font-size: 11px;
            margin-left: 2px;
        }}
        .versus-card {{
            min-width: 0;
            width: 42px;
            min-height: 96px;
            padding: 8px 4px;
            border-radius: 18px;
        }}
        .versus-main {{
            font-size: 16px;
        }}
        .versus-sub {{
            display: none;
        }}
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

st.markdown(
    make_running_score_html(st.session_state.selected_cell),
    unsafe_allow_html=True,
)

if cell:
    score_dialog(cell)

st.divider()

# PDF出力
pdf_buffer = create_score_sheet_pdf(team_a_name, team_b_name)

st.download_button(
    "📄 PDFをダウンロード",
    data=pdf_buffer,
    file_name="score_sheet.pdf",
    mime="application/pdf",
)

st.divider()

if st.button("🧹 入力をすべてリセット", type="secondary"):
    st.session_state.scores = default_scores()
    st.session_state.selected_cell = ""
    save_scores()
    st.query_params.clear()
    st.rerun()
