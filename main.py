import streamlit as st
import pandas as pd
import copy
import time

# button_cssは使用していない　st.markdown(button_css, unsafe_allow_html=True)
button_css = f"""
<style>
  div.stButton > button:first-child  {{
    font-weight  : bold                ;/* 文字：太字                   */
    border       :  5px solid #f36     ;/* 枠線：ピンク色で5ピクセルの実線 */
    border-radius: 10px 10px 10px 10px ;/* 枠線：半径10ピクセルの角丸     */
    background   : #ddd                ;/* 背景色：薄いグレー            */
  }}
</style>
"""

st.title('ランニングスコア :basketball:')
st.header('得点・アシスト集計画面')
st.caption('得点・アシストなどを行った選手を登録して下さい。')

markdown = """
\n
"""
bibsType_help_txt = '''
        ビブスType詳細については、下記を参照して下さい。
        
        | ビブス | 説明 | 
        |:-----|:-----|
        |ドバスOriginal | 色は赤と青。赤色ビブスには【DOBASU】と青色ビブスには【Thunder】と記載されている。|
        | SPALDING | 色はネイビーとピンク。胸の当たりにSPALDINGのロゴがあります。| 
        | 無地 | 色は水色とオレンジ。 無地です|    
        '''

@st.cache_resource
def cache_lst():
    lst = []
    return lst
lst = cache_lst()

with st.form (key = 'input_form'):
 classType= st.radio('CLASS', ('初級', '中級'), horizontal=True)
 st.write(markdown)
 team = st.radio('TEAM', ('Red', 'Blue'), horizontal=True)
 st.write(markdown)
 bibsType = st.radio('ビブスType', ('ドバスOriginal', 'SPALDING', '無地'), horizontal=True, help = bibsType_help_txt)
 st.write(markdown)
 uniformNumber = st.selectbox('背番号', ('00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '21', '31', '32', '35', '--'))
 st.write(markdown)
 option = st.selectbox('得点・アシスト', ('ツーポイント', 'スリーポイント', 'フリースロー', 'アシスト', 'ブロック', 'リバウンド', 'スティール', 'ファール'))
 st.write(markdown)
 
 col1, col2, col3 = st.columns([2, 1, 1])
 with col1:
  submit_btn = st.form_submit_button('登録')
 with col2:
  listAll_btn = st.form_submit_button('一覧表示')
 with col3:
  DeleteLastRow_btn = st.form_submit_button('最終行を削除')
 
 if submit_btn:
     try:
      lst.append([classType, team, bibsType, uniformNumber, option])
      df = pd.DataFrame(lst)
      df.columns = ['CLASS', 'TEAM', 'ビブスType', '背番号', '得点・アシスト']
      st.dataframe(df)
      #  st.write(lst)
     except:
      # エラーメッセージ
      st.error('データ登録時にエラーが発生しました。')
      
 if listAll_btn:
     try:
      df = pd.DataFrame(lst)
      df.columns = ['CLASS', 'TEAM', 'ビブスType', '背番号', '得点・アシスト']
      st.dataframe(df)
      #  st.write(lst)
     except:
      # エラーメッセージ
      st.warning('表示するデータがありません。データを登録して下さい')

 if DeleteLastRow_btn: 
     try:
      lst.pop(-1)
      df = pd.DataFrame(lst)
      df.columns = ['CLASS', 'TEAM', 'ビブスType', '背番号', '得点・アシスト']
      st.dataframe(df)
     #  st.write(lst)
     except:
     # エラーメッセージ
      st.warning('表示するデータがありません。データを登録して下さい')

check = st.checkbox('最終行以外を削除する場合はチェックする')
if check: 
 delete_num = st.text_input('削除する行番号を入力して削除ボタンを押下')
 col1, col2 = st.columns([4, 1])
 with col1:
  delete_btn = st.button('削除')
 with col2:
  clear_btn = st.button('すべてクリア')

 if delete_btn:
     try:
      lst.pop(int(delete_num))
     except:
      st.error('データ削除時にエラーが発生しました。数値で入力するが存在する行番号を設定して下さい。')

 if clear_btn:
     try:
      st.cache_resource.clear()
     except:
      st.error('データ削除時にエラーが発生しました。')
 
 st.write(markdown)
 st.write(markdown)
 
st.write(markdown)
submit_btn4 = st.button('集計')

if submit_btn4:

 text = st.empty()
 bar = st.progress(0)
 for i in range(100):
  text.text(f" 集計中 { i + 1 } / 100 % ")
  bar.progress(i + 1)
  time.sleep(0.01)
  
 text.text('completed!')
 st.write(markdown)
 st.balloons()
 
 lst2 = []
 lst3 = []
 lst1 = []
 lstA = []
 lstB = []
 lstR = []
 lstS = []
 lstF = []
 strlist = []
 sumlist = []

 strlist = copy.deepcopy(lst)
 
 for item in strlist:
     if item[4] == 'ツーポイント':
         item[4] = 2
         lst2.append(item)
     elif item[4] == 'スリーポイント':
         item[4] = 3
         lst3.append(item)
     elif item[4] == 'フリースロー':
         item[4] = 1
         lst1.append(item)
     elif item[4] == 'アシスト':
         item[4] = 1
         lstA.append(item)
     elif item[4] == 'ブロック':
         item[4] = 1
         lstB.append(item)
     elif item[4] == 'リバウンド':
         item[4] = 1
         lstR.append(item)
     elif item[4] == 'スティール':
         item[4] = 1
         lstS.append(item)
     elif item[4] == 'ファール':
         item[4] = 1
         lstF.append(item)
         
 teamPointList = []
 classPointlist = []
 tmpPointList = []
 tmpPointList += lst1 + lst2 + lst3
 
 for item in tmpPointList:
     teamPointList.append([item[1], item[4]])
     classPointlist.append([item[0], item[1], item[4]])

 st.write('# 集計結果！📉 ')
 st.write(markdown)
 
 df = pd.DataFrame(teamPointList, columns=['TEAM', '合計得点'])
 st.write('【 :red[TEAM] 】ごとの得点の集計結果はこちら 👇')
 st.write(df.groupby(['TEAM']).sum())  

 df = pd.DataFrame(classPointlist, columns=['CLASS', 'TEAM', '合計得点'])
 st.write('【 :red[CLASS] 】ごとの得点の集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM']).sum())
 
 sumlist += lst1 + lst2 + lst3
 df = pd.DataFrame(sumlist, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計得点'])
 st.write('【 :red[すべて] 】の得点の集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())
          
 df = pd.DataFrame(lst2, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計得点'])
 st.write('【 :orange[ツーポイント] 】のみの集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lst3, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計得点'])
 st.write('【:orange[スリーポイント]】のみの集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lst1, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計得点'])
 st.write('【 :orange[フリースロー] 】のみの集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstA, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計回数'])
 st.write('【 :violet[アシスト] 】の集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstB, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計回数'])
 st.write('【 :violet[ブロック] 】の集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstR, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計回数'])
 st.write('【 :violet[リバウンド] 】の集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstS, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計回数'])
 st.write('【 :violet[スティール] 】の集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstF, columns=['CLASS', 'TEAM', 'ビブスType', '背番号', '合計回数'])
 st.write('【 :violet[ファール] 】の集計結果はこちら 👇')
 st.write(df.groupby(['CLASS', 'TEAM', 'ビブスType', '背番号']).sum())

