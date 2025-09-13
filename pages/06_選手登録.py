import streamlit as st
import pandas as pd
import os

from app_auth import require_login, render_userbox

require_login()     # ← 未ログインならログインへ誘導して stop
render_userbox()    # ← サイドバーに「ログイン中」「ログアウト」表示

PLAYER_CSV = 'players.csv'

# --- スタイリング CSS（円形ボタン含む） ---
st.markdown("""
<style>
  html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f4f7fa;
  }
  .circle-button {
    display: inline-block;
    border-radius: 50%;
    width: 100px;
    height: 100px;
    line-height: 100px;
    text-align: center;
    font-weight: bold;
    background: linear-gradient(45deg, #ffcc00, #ff0066);
    color: white;
    box-shadow: 0 5px 0 #e6d900;
    transition: all 0.2s ease;
  }
  .circle-button:hover {
    transform: translate(0, 3px);
    box-shadow: 0 2px 0 #e6d900;
  }
  .confirm-box {
    padding: 1rem;
    border: 2px dashed #f36;
    background-color: #fff0f5;
    border-radius: 10px;
    margin-bottom: 1rem;
  }
  .confirm-box p {
    font-weight: bold;
    color: #d33;
  }
</style>
""", unsafe_allow_html=True)

st.title("🏀選手登録")
st.caption("選手の背番号・名前・チーム・ビブスType・CLASSを登録します")

# 入力フォーム
with st.form(key='player_register_form'):
    col1, col2 = st.columns(2)
    with col1:
        uniform_number = st.text_input("背番号", max_chars=4)
        player_name = st.text_input("プレイヤー名")
    with col2:
        team = st.selectbox("チーム", ("Red", "Blue"))
        bibs_type = st.selectbox("ビブスType", ("ドバスOriginal", "SPALDING", "無地"))

    class_type = st.radio("CLASS", ("初級", "中級", "上級"), horizontal=True)
    submit = st.form_submit_button("✅ 選手を登録")

# データ保存処理
def save_player(uniform_number, player_name, team, bibs_type, class_type):
    new_entry = pd.DataFrame([{
        '背番号': uniform_number,
        'プレイヤー名': player_name,
        'TEAM': team,
        'ビブスType': bibs_type,
        'CLASS': class_type
    }])
    if os.path.exists(PLAYER_CSV):
        df = pd.read_csv(PLAYER_CSV, dtype=str)
        df = pd.concat([df, new_entry], ignore_index=True)
    else:
        df = new_entry
    df.drop_duplicates(subset=['背番号', 'プレイヤー名', 'TEAM', 'ビブスType', 'CLASS'], inplace=True)
    df.to_csv(PLAYER_CSV, index=False)

if submit:
    if uniform_number and player_name:
        save_player(uniform_number, player_name, team, bibs_type, class_type)
        st.success(f"🎉 選手 {player_name}（背番号: {uniform_number}）を登録しました！")
        st.rerun()
    else:
        st.warning("⚠️ 背番号とプレイヤー名は必須です")

# 現在の登録選手一覧と削除機能
st.write("\n")
st.subheader("📋 登録済み選手一覧")
if os.path.exists(PLAYER_CSV):
    df = pd.read_csv(PLAYER_CSV, dtype=str)
    st.dataframe(df)

    st.write("\n")
    st.markdown("### ❌ 選手の削除")
    options = df.apply(lambda row: f"{row['背番号']} - {row['プレイヤー名']} - {row['TEAM']} - {row['ビブスType']} - {row['CLASS']}", axis=1).tolist()
    selected_to_delete = st.selectbox("削除する選手を選択", options)

    confirm_delete = st.checkbox("⚠️ 本当にこの選手を削除しますか？")
    delete_key = f"delete_{selected_to_delete}"  # 重複しないキーを生成

    if st.button("❌ この選手を削除", key=delete_key) and confirm_delete:
        try:
            num, name, team_sel, bibs_sel, class_sel = selected_to_delete.split(" - ")
            df = df[~(
                (df['背番号'] == num) &
                (df['プレイヤー名'] == name) &
                (df['TEAM'] == team_sel) &
                (df['ビブスType'] == bibs_sel) &
                (df['CLASS'] == class_sel)
            )]
            df.to_csv(PLAYER_CSV, index=False)
            st.success(f"✅ 選手 {name}（背番号: {num}）を削除しました！")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 削除時にエラーが発生しました: {e}")
else:
    st.info("まだ選手は登録されていません")
