# main.py
import streamlit as st

from app_auth import require_login, render_userbox

require_login()
render_userbox()

st.set_page_config(
    page_title="\U0001F3C0RUNNING SCORE",
    layout="centered",
    initial_sidebar_state="expanded"
)

import pandas as pd
import time
import sqlite3
import streamlit.components.v1 as components

from lib_db import (
    get_conn, inject_css, inject_mobile_big_ui, notify,
    add_event_sql, delete_event_by_id, delete_events_by_ids,
    read_df_sql, read_recent_df, export_events_csv, backup_sqlite,
    wipe_all_data, get_score_red_blue, POINT_MAP, STAT_SET, FOUL_SET
)

inject_css()
inject_mobile_big_ui()

DB_PATH = 'players.db'

def load_players_from_sqlite():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM players", conn)
    df["表示"] = df.apply(lambda row: f"{row['uniform_number']} - {row['player_name']} - {row['bibs_type']}", axis=1)
    df.rename(columns={
        "uniform_number": "背番号",
        "player_name": "プレイヤー名",
        "team": "TEAM",
        "bibs_type": "ビブスType",
        "class_type": "CLASS"
    }, inplace=True)
    return df

def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            try:
                st.toast("\U0001F504 画面を更新してください（ブラウザの再読み込み）", icon="\U0001F504")
            except Exception:
                st.warning("\U0001F504 画面を更新してください（Ctrl/Cmd + R）")

conn = get_conn()
players_df = load_players_from_sqlite()

st.session_state.setdefault("last_insert_id", None)
st.session_state.setdefault("last_action_ts", 0)

st.title("\U0001F3C0RUNNING SCORE")
red_pts, blue_pts = get_score_red_blue(conn)
st.markdown(f"""
<div class="scorebar">
  <div class="scorebox">
    <div class="info">\U0001F4CA TOTAL SCORE</div>
    <div>
      <span class="scorechip red">Red: {red_pts}</span>
      <span class="scorechip blue">Blue: {blue_pts}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

classType = st.radio('\U0001F680 CLASS', ('初級','中級','上級'), horizontal=True, key="class_radio")
team      = st.radio('\U0001F1EA TEAM',  ('Red','Blue'), horizontal=True, key="team_radio")
quarter   = st.selectbox('\u23F1\uFE0F Quarter', ('Q1','Q2','Q3','Q4','OT'), key="quarter_select")

filtered = players_df[(players_df['CLASS']==classType) & (players_df['TEAM']==team)].copy()
if not filtered.empty:
    display_options = filtered['表示'].tolist()
    selected_player = st.selectbox("\u26C9\uFE0F‍♂\uFE0F 選手（背番号 - 名前 - ビブス）", display_options, key="player_select")
    row = filtered[filtered['表示']==selected_player].iloc[0]
    uniformNumber = row['背番号']; playerName = row['プレイヤー名']; bibsType = row['ビブスType']
else:
    st.warning(f"CLASS={classType} / TEAM={team} の選手がいません。")
    uniformNumber = '--'; playerName = ''; bibsType = ''

def add_event(action_label: str):
    now = time.time()
    if now - st.session_state.last_action_ts < 0.35:
        return
    if uniformNumber == '--':
        st.error('選手が未選択です。'); return
    rid = add_event_sql(conn, classType, team, bibsType, uniformNumber, playerName, action_label, quarter)
    st.session_state.last_insert_id = rid
    st.session_state.last_action_ts = now
    notify(f"登録: {playerName} / {action_label} / {quarter}", icon="✅")

TAB_OPTIONS = ["\U0001F9EE 得点", "\U0001F4C8 スタッツ", "\U0001F6A8 反則"]
active_tab_default = st.session_state.get("active_tab", TAB_OPTIONS[0])
tab = st.radio("表示タブ", TAB_OPTIONS, horizontal=True,
               index=TAB_OPTIONS.index(active_tab_default) if active_tab_default in TAB_OPTIONS else 0,
               key="active_tab_radio", label_visibility="collapsed")
st.session_state["active_tab"] = tab

if tab == "\U0001F9EE 得点":
    st.caption("タップで登録")
    c1, c2, c3 = st.columns(3)
    with c1:  st.button("\U0001F3C0 3pt", on_click=add_event, args=("3pt",))
    with c2:  st.button("\U0001F3C0 2pt", on_click=add_event, args=("2pt",))
    with c3:  st.button("\U0001F3C0 1pt", on_click=add_event, args=("1pt",))

elif tab == "\U0001F4C8 スタッツ":
    st.caption("タップで登録")
    r1c1, r1c2 = st.columns(2); r2c1, r2c2 = st.columns(2)
    with r1c1: st.button("\U0001F170\uFE0F アシスト", on_click=add_event, args=("アシスト",))
    with r1c2: st.button("\U0001F9F1 ブロック", on_click=add_event, args=("ブロック",))
    with r2c1: st.button("\U0001F3D7️ リバウンド", on_click=add_event, args=("リバウンド",))
    with r2c2: st.button("\U0001F575️ スティール", on_click=add_event, args=("スティール",))

elif tab == "\U0001F6A8 反則":
    st.caption("タップで登録")
    f1, f2 = st.columns(2)
    with f1: st.button("\U0001F6A8 ファール", on_click=add_event, args=("ファール",))
    with f2: st.button("\u267B\uFE0F ターンオーバー", on_click=add_event, args=("ターンオーバー",))

# ─── ログ表示（最新N件 / 全件）＋ 管理ツール（Expanderに集約） ───
st.markdown("---")
st.subheader("📋 ログ表示")
view_mode = st.radio("表示モード", ("最新N件", "全件"), horizontal=True, key="log_view_mode")
if view_mode == "最新N件":
    N = st.number_input("表示する件数（最新N件）", min_value=10, max_value=5000, value=10, step=10, key="log_top_n")
    df_show = read_recent_df(conn, n=int(N))
else:
    df_show = read_df_sql(conn)

if not df_show.empty:
    order = ['id','created_at','CLASS','TEAM','ビブスType','背番号','名前','得点・アシスト','クォーター']
    order = [c for c in order if c in df_show.columns] + [c for c in df_show.columns if c not in order]
    df_show = df_show[order].copy()
    df_show['id'] = df_show['id'].astype(int)

    # 表（編集可/不可）は従来どおり
    supports_data_editor = hasattr(st, "data_editor")

    if supports_data_editor:
        df_edit = df_show.copy()
        df_edit['削除'] = False
        edited = st.data_editor(df_edit, hide_index=True, use_container_width=True, height=480)
    else:
        st.dataframe(df_show, use_container_width=True, height=480)

    # ★ 管理ツールをひとまとめの Expander に格納
    with st.expander("🧰 管理ツール（削除・取り消し・エクスポート・バックアップ・全消去）", expanded=False):

        # ① 行削除（チェック／マルチセレクト／ID指定）
        st.markdown("**🧹 行削除**")
        if supports_data_editor:
            colD1, colD2 = st.columns([1,2])
            with colD1:
                if st.button("🗑️ チェックした行を削除", type="primary", use_container_width=True):
                    ids = edited.loc[edited['削除'] == True, 'id'].astype(int).tolist()
                    if ids:
                        delete_events_by_ids(conn, ids)
                        st.success(f"{len(ids)} 件を削除しました。")
                        safe_rerun()  # ← 置き換え
                    else:
                        st.warning("削除対象が選ばれていません。")
            with colD2:
                id_text = st.text_input("id をカンマ区切りで指定（例: 101,102,120）", value="", key="id_delete_input")
                if st.button("🧹 指定した id を削除", use_container_width=True):
                    try:
                        ids = [int(s.strip()) for s in id_text.split(",") if s.strip()]
                    except ValueError:
                        ids = []
                    if ids:
                        delete_events_by_ids(conn, ids)
                        st.success(f"id={ids} を削除しました。")
                        safe_rerun()  # ← 置き換え
                    else:
                        st.warning("id の指定が正しくありません。半角数字をカンマで区切って入力してください。")
        else:
            del_ids = st.multiselect("削除する id を選択", df_show['id'].tolist(), key="del_ids_multiselect")
            colD1, colD2 = st.columns([1,2])
            with colD1:
                if st.button("🗑️ 選択した id を削除", type="primary", use_container_width=True):
                    if del_ids:
                        delete_events_by_ids(conn, del_ids)
                        st.success(f"{len(del_ids)} 件を削除しました。")
                        safe_rerun()  # ← 置き換え
                    else:
                        st.warning("削除対象が選ばれていません。")
            with colD2:
                id_text = st.text_input("id をカンマ区切りで指定（例: 101,102,120）", value="", key="id_delete_input_fb")
                if st.button("🧹 指定した id を削除（互換）", use_container_width=True):
                    try:
                        ids = [int(s.strip()) for s in id_text.split(",") if s.strip()]
                    except ValueError:
                        ids = []
                    if ids:
                        delete_events_by_ids(conn, ids)
                        st.success(f"id={ids} を削除しました。")
                        safe_rerun()  # ← 置き換え
                    else:
                        st.warning("id の指定が正しくありません。")

        st.markdown("---")

        # ② 直前の登録を取り消す
        st.markdown("**↩️ 直前取り消し**")
        if st.button("↩️ 直前の登録を取り消す", use_container_width=True):
            if st.session_state.last_insert_id:
                delete_event_by_id(conn, st.session_state.last_insert_id)
                st.success("直前の1件を取り消しました。")
                st.session_state.last_insert_id = None
                safe_rerun()  # ← 置き換え
            else:
                st.warning("この端末で直近に登録した1件がありません。")

        st.markdown("---")

        # ③ エクスポート & バックアップ
        st.markdown("**💾 エクスポート & バックアップ**")
        colE1, colE2 = st.columns(2)
        with colE1:
            fname, csv_bytes = export_events_csv(conn)
            st.download_button("⬇️ CSVエクスポート（全データ）", data=csv_bytes, file_name=fname, mime="text/csv", use_container_width=True)
        with colE2:
            if st.button("🗂️ SQLiteバックアップ作成", use_container_width=True):
                bak_name, bak_bytes = backup_sqlite(conn)
                st.download_button("⬇️ バックアップをダウンロード", data=bak_bytes, file_name=bak_name, mime="application/octet-stream", use_container_width=True)

        st.markdown("---")

        # ④ 全データ削除
        st.markdown("**⚠️ データリセット（events 全削除）**")
        colx, coly = st.columns([2,1])
        with colx:
            confirm = st.text_input("確認のため、DELETE と入力してください（全角不可）", value="")
        with coly:
            if st.button("🗑️ 全データ削除", type="primary", use_container_width=True):
                if confirm.strip() == "DELETE":
                    wipe_all_data(conn)
                    st.session_state.last_insert_id = None
                    st.success("全データを削除しました。")
                    safe_rerun()  # ← 置き換え
                else:
                    st.error("確認文字が一致しません。'DELETE' と入力してください。")

    st.caption(f"表示: {len(df_show)} 件（※削除後は自動更新）")
else:
    st.info("表示できるデータがありません。")

# ─────────────────────────────────────────
# 集計ページへ（再集計して遷移：全方位フォールバック）
# ─────────────────────────────────────────
def _streamlit_ver_ge(major, minor):
    try:
        v = tuple(map(int, st.__version__.split(".")[:2]))
        return v >= (major, minor)
    except Exception:
        return False

def go_to_agg_page():
    import time as _t
    st.session_state["agg_refresh_key"] = _t.time()  # 集計ページ側で「再集計しました」トースト用

    # 1) 新しめの環境：st.switch_page（相対パス指定）
    if _streamlit_ver_ge(1, 30):
        try:
            st.switch_page("pages/01_集計.py")
            return
        except Exception:
            pass

    # 2) st.page_link があるなら、不可視リンクを自動クリック（hrefはStreamlitが正しく生成）
    if hasattr(st, "page_link"):
        hide = st.empty()
        with hide:
            st.markdown('<div id="__autonav__" style="display:none">', unsafe_allow_html=True)
            st.page_link("pages/01_集計.py", label="__AUTO_NAV_AGG__", icon="📊")
            st.markdown('</div>', unsafe_allow_html=True)

        components.html("""
        <script>
          function clickHiddenLink(){
            try{
              const doc = window.parent.document;
              const as = Array.from(doc.querySelectorAll('a'));
              const target = as.find(a => (a.innerText||'').includes('__AUTO_NAV_AGG__'));
              if (target){ target.click(); return true; }
            }catch(e){}
            return false;
          }
          setTimeout(clickHiddenLink, 150);
          setTimeout(clickHiddenLink, 600);
          setTimeout(clickHiddenLink, 1200);
        </script>
        """, height=0)
        return

    # 3) 最終手段：サイドバーの「集計」リンクを探してクリック（旧環境向け）
    components.html("""
    <script>
      function clickSidebarAgg(){
        try{
          const doc = window.parent.document;
          const as = Array.from(doc.querySelectorAll('a'));
          const enc = encodeURI('01_集計');
          const target = as.find(a =>
            (a.innerText && a.innerText.includes('集計')) ||
            (a.href && (a.href.includes('01_%E9%9B%86%E8%A8%88') || a.href.includes(enc)))
          );
          if (target){ target.click(); return true; }
        }catch(e){}
        return false;
      }
      setTimeout(clickSidebarAgg, 150);
      setTimeout(clickSidebarAgg, 600);
      setTimeout(clickSidebarAgg, 1200);
    </script>
    """, height=0)

# ボタン本体（配置はお好みでOK：スコアバー直下が見栄え◎）
go_cols = st.columns([1, 2, 1])
with go_cols[1]:
    st.button("📊 集計ページ（再集計して開く）", type="primary", on_click=go_to_agg_page)

# 念のための手動リンク
if hasattr(st, "page_link"):
    st.page_link("pages/01_集計.py", label="➡️ 手動で開く（集計ページ）")
