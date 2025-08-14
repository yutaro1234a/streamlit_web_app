import streamlit as st
import pandas as pd
import copy
import time
import os

PLAYER_CSV = 'players.csv'
SCORE_CSV = 'score_log.csv'

st.title('🏀 ランニングスコア集計アプリ')
st.header('✨ 得点・アシスト登録＆集計画面')
st.caption('以下の選手情報とプレイ内容を入力してください')

@st.cache_resource
def cache_lst():
    if os.path.exists(SCORE_CSV):
        return pd.read_csv(SCORE_CSV).values.tolist()
    return []
lst = cache_lst()

# プレイヤーリストの読み込み
def load_players():
    if os.path.exists(PLAYER_CSV):
        df = pd.read_csv(PLAYER_CSV, dtype=str)
        df['背番号'] = df['背番号'].astype(str)
        df['表示'] = df['背番号'] + ' - ' + df['プレイヤー名'] + '（' + df['ビブスType'] + '）'
        return df
    return pd.DataFrame()

players_df = load_players()

# CLASSとTEAMの選択
classType = st.radio('🏫 CLASS 選択', ('初級', '中級', '上級'), horizontal=True, key="class_radio")
team = st.radio('🟥 TEAM 選択', ('Red', 'Blue'), horizontal=True, key="team_radio")

# フィルタリングされた選手の選択
if not players_df.empty:
    filtered_players = players_df[(players_df['CLASS'] == classType) & (players_df['TEAM'] == team)]

    if not filtered_players.empty:
        display_options = filtered_players['表示'].tolist()
        selected_player = st.selectbox(
            '🙋‍♂️ 選手を選択（背番号 - 名前 - ビブス）', 
            display_options,
            key=f"player_select_dynamic"
        )
        selected_row = filtered_players[filtered_players['表示'] == selected_player].iloc[0]
        uniformNumber = selected_row['背番号']
        playerName = selected_row['プレイヤー名']
        bibsType = selected_row['ビブスType']
    else:
        st.warning(f"選択されたCLASS（{classType}）とTEAM（{team}）の選手が登録されていません。")
        uniformNumber = '--'
        playerName = ''
else:
    st.warning('選手が登録されていません。先に登録してください。')
    uniformNumber = '--'
    playerName = ''

option = st.selectbox('🎯 プレイ内容', ('ツーポイント', 'スリーポイント', 'フリースロー', 'アシスト', 'ブロック', 'リバウンド', 'スティール', 'ファール'))

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    submit_btn = st.button('✅ 登録')
with col2:
    listAll_btn = st.button('📋 一覧表示')
with col3:
    DeleteLastRow_btn = st.button('❌ 最終行を削除')

if submit_btn:
    try:
        lst.append([classType, team, bibsType, uniformNumber, playerName, option])
        df = pd.DataFrame(lst, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '名前', '得点・アシスト'])
        df.to_csv(SCORE_CSV, index=False)
        st.success('✅ データを登録しました')
        st.dataframe(df)
    except:
        st.error('❌ データ登録時にエラーが発生しました。')

if listAll_btn:
    if lst:
        df = pd.DataFrame(lst, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '名前', '得点・アシスト'])
        st.dataframe(df)
    else:
        st.warning('📭 表示するデータがありません。データを登録して下さい')

if DeleteLastRow_btn:
    if lst:
        lst.pop(-1)
        df = pd.DataFrame(lst, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '名前', '得点・アシスト'])
        df.to_csv(SCORE_CSV, index=False)
        st.success('🗑️ 最終行を削除しました')
        st.dataframe(df)
    else:
        st.warning('削除できるデータがありません。')

st.markdown("---")
submit_btn4 = st.button('📊 集計')

if submit_btn4:
    text = st.empty()
    bar = st.progress(0)
    for i in range(100):
        text.text(f" 集計中 {i + 1} / 100 % ")
        bar.progress(i + 1)
        time.sleep(0.005)

    text.text('✅ 集計完了!')
    st.balloons()

    strlist = copy.deepcopy(lst)
    得点項目 = {'ツーポイント': 2, 'スリーポイント': 3, 'フリースロー': 1}

    得点データ = []
    その他データ = []

    for item in strlist:
        record = item.copy()
        action = record[5]
        if action in 得点項目:
            record[5] = 得点項目[action]
            得点データ.append(record)
        else:
            その他データ.append(record[:5] + [1, action])

    df_score = pd.DataFrame(得点データ, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '名前', '得点'])
    df_other = pd.DataFrame(その他データ, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '名前', '回数', '項目'])

    st.subheader('📌 TEAMごとの得点')
    st.dataframe(df_score.groupby('TEAM')['得点'].sum().reset_index())

    st.subheader('📌 CLASS + TEAMごとの得点')
    st.dataframe(df_score.groupby(['CLASS', 'TEAM'])['得点'].sum().reset_index())

    st.subheader('📌 選手ごとの得点')
    st.dataframe(df_score.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号', '名前'])['得点'].sum().reset_index())

    if not df_other.empty:
        st.subheader('📌 選手ごとのその他プレイ回数')
        st.dataframe(df_other.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号', '名前', '項目'])['回数'].sum().reset_index())
