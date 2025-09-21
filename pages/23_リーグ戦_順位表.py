import streamlit as st
import sqlite3
import pandas as pd
from app_auth import render_userbox

st.set_page_config(layout="wide")  # モバイルでも横幅対応

# --- ログインチェック ---
if "auth_user" not in st.session_state:
    st.switch_page("pages/00_ログイン.py")

try:
    render_userbox(key="logout_button_league_standings")
except TypeError:
    render_userbox()

DB_PATH = "league.db"

# --- データ取得 ---
def fetch_matches():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM league_matches", conn)

# --- 順位表計算 ---
def calculate_standings(df_matches):
    if df_matches.empty:
        return pd.DataFrame()

    col_t1, col_t2 = "team_1", "team_2"
    col_s1, col_s2 = "score_1", "score_2"
    teams = set(df_matches[col_t1].tolist() + df_matches[col_t2].tolist())
    stats = {team: {"試合数": 0, "勝": 0, "敗": 0, "引分": 0, "得点": 0, "失点": 0} for team in teams}

    for _, row in df_matches.iterrows():
        t1, t2, s1, s2 = row[col_t1], row[col_t2], row[col_s1], row[col_s2]
        stats[t1]["試合数"] += 1
        stats[t2]["試合数"] += 1
        stats[t1]["得点"] += s1
        stats[t1]["失点"] += s2
        stats[t2]["得点"] += s2
        stats[t2]["失点"] += s1
        if s1 > s2:
            stats[t1]["勝"] += 1
            stats[t2]["敗"] += 1
        elif s1 < s2:
            stats[t2]["勝"] += 1
            stats[t1]["敗"] += 1
        else:
            stats[t1]["引分"] += 1
            stats[t2]["引分"] += 1

    recs = []
    for team, d in stats.items():
        diff = d["得点"] - d["失点"]
        recs.append({
            "チーム": team,
            "試合数": d["試合数"],
            "勝": d["勝"],
            "敗": d["敗"],
            "引分": d["引分"],
            "得点": d["得点"],
            "失点": d["失点"],
            "得失点差": diff
        })

    df = pd.DataFrame(recs)
    df = df.sort_values(by=["勝", "得失点差"], ascending=False).reset_index(drop=True)
    df.insert(0, "順位", df.index + 1)
    return df

# --- 星取表（記号＋得点）作成 ---
def build_star_table_with_scores(df_matches, teams):
    matrix = pd.DataFrame({t: ["-" for _ in teams] for t in teams}, index=teams, columns=teams)
    for _, row in df_matches.iterrows():
        t1, t2 = row["team_1"], row["team_2"]
        s1, s2 = row["score_1"], row["score_2"]
        icon1, icon2 = ("○", "●") if s1 > s2 else ("●", "○") if s1 < s2 else ("△", "△")
        matrix.at[t1, t2] = f"{icon1}\n{s1}-{s2}"
        matrix.at[t2, t1] = f"{icon2}\n{s2}-{s1}"
    return matrix

# --- 順位表スタイル：シンプル＆ポップ＆チームアイコン追加 ---
def style_standings_fancy(df):
    df_display = df.copy()

    # チーム名にアイコン（絵文字）を付ける例（任意で編集可能）
    team_icons = {
        "A": "🐙 A",
        "B": "🦑 B",
        "C": "🐡 C",
        "D": "🦀 D"
    }
    df_display["チーム"] = df_display["チーム"].map(lambda x: team_icons.get(x, x))

    styler = df_display.style.set_properties(**{
        "text-align": "center",
        "border": "1px solid #ccc",
        "font-family": "'Segoe UI', sans-serif",
        "font-size": "13px",
        "padding": "8px",
        "white-space": "nowrap",
        "background-color": "#ffffff"
    })
    return styler

# --- 星取表スタイル（スマホ向け調整） ---
def style_star_table(df):
    def highlight_cells(val):
        if isinstance(val, str):
            if "○" in val:
                return "background-color: #d4edda; color: #155724; text-align: center; white-space: pre-wrap; font-size: 12px;"
            elif "●" in val:
                return "background-color: #f8d7da; color: #721c24; text-align: center; white-space: pre-wrap; font-size: 12px;"
            elif "△" in val:
                return "background-color: #fefefe; color: #6c757d; text-align: center; white-space: pre-wrap; font-size: 12px;"
        return "text-align: center; white-space: pre-wrap; font-size: 12px;"

    styled = df.style.applymap(highlight_cells)
    styled.set_properties(**{
        "border": "1px solid #ccc",
        "font-family": "'Segoe UI', sans-serif",
        "font-size": "12px"
    })
    return styled

# --- UI 表示部分 ---
st.title("📈 リーグ戦：順位表 + 星取表（勝敗記号＋得点）")
st.caption("星取表は上段に勝敗記号、下段に得点スコアを表示！")

df_matches = fetch_matches()

if df_matches.empty:
    st.info("まだ試合結果が登録されていません。")
else:
    teams = sorted(set(df_matches["team_1"].tolist() + df_matches["team_2"].tolist()))

    st.subheader("⭐ 順位表")
    df_standings = calculate_standings(df_matches)
    st.write(style_standings_fancy(df_standings).hide(axis="index").to_html(), unsafe_allow_html=True)

    st.subheader("📋 星取表（記号上段／得点下段）")
    df_star = build_star_table_with_scores(df_matches, teams)
    st.write(style_star_table(df_star).to_html(), unsafe_allow_html=True)