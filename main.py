import streamlit as st
import pandas as pd
import copy

st.title('ランニングスコア')
st.header('得点・サポート登録画面')
st.subheader('得点・サポート登録画面')
st.caption('得点・サポートなどを行った選手を登録して下さい。')

@st.cache_resource
def cache_lst():
    lst = []
    return lst
lst = cache_lst()

with st.form (key = 'input_form'):
 team = st.radio('TEAM', ('Red', 'Blue'), horizontal=True)
 classType= st.radio('CLASS', ('初級', '中級'), horizontal=True)
 bibsType = st.radio('ビブスType', ('無地', '無地以外'), horizontal=True)
 uniformNumber = st.selectbox('背番号', ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10'))
 option = st.selectbox('種類', ('ツーポイント', 'スリーポイント', 'フリースロー', 'アシスト', 'ブロック', 'リバウンド', 'スティール', 'ファール'))
 markdown = """ 
 """
 st.write(markdown)
 col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
 with col1:
  submit_btn = st.form_submit_button('登録')
 with col2:
  submit_btn2 = st.form_submit_button('一覧表示')
 with col3:
  submit_btn3 = st.form_submit_button('最終行を削除')
 with col4:
  clear_btn = st.form_submit_button('ALLクリア')
 
 if submit_btn2: 
     df = pd.DataFrame(lst)
     df.columns = ['TEAM', 'CLASS', 'ビブスType', '背番号', '種類']
     st.dataframe(df)
    #  st.write(lst)

 if submit_btn: 
     lst.append([team, classType, bibsType, uniformNumber, option])
     df = pd.DataFrame(lst)
     df.columns = ['TEAM', 'CLASS', 'ビブスType', '背番号', '種類']
     st.dataframe(df)
    #  st.write(lst)

 if submit_btn3: 
     lst.pop(-1)
     df = pd.DataFrame(lst)
     df.columns = ['TEAM', 'CLASS', 'ビブスType', '背番号', '種類']
     st.dataframe(df)
    #  st.write(lst)

 if clear_btn: 
     st.cache_resource.clear()

check = st.checkbox('最終行以外を削除する場合はチェックをつける')
if check:
 delete_num = st.text_input('削除する行番号を入力')
 delete_btn = st.button('削除')
 
 if delete_btn:
     lst.pop(int(delete_num))

submit_btn4 = st.button('集計')
if submit_btn4:
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
          
 df = pd.DataFrame(lst2)
 df = pd.DataFrame(lst2, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計得点'])
 markdown = """
 ツーポイントの結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lst3)
 df = pd.DataFrame(lst3, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計得点'])
 markdown = """
 スリーポイントの結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lst1)
 df = pd.DataFrame(lst1, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計得点'])
 markdown = """
 フリースローの結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())


 sumlist += lst1 + lst2 + lst3
 df = pd.DataFrame(sumlist)
 df = pd.DataFrame(sumlist, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計得点'])
 markdown = """
 すべての結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())


 df = pd.DataFrame(lstA)
 df = pd.DataFrame(lstA, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計回数'])
 markdown = """
 アシストの結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstB)
 df = pd.DataFrame(lstB, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計回数'])
 markdown = """
 ブロックの結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstR)
 df = pd.DataFrame(lstR, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計回数'])
 markdown = """
 リバウンドの結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstS)
 df = pd.DataFrame(lstS, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計回数'])
 markdown = """
 スティールの結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())

 df = pd.DataFrame(lstF)
 df = pd.DataFrame(lstF, columns=['TEAM', 'CLASS', 'ビブスType', '背番号', '合計回数'])
 markdown = """
 ファールの結果はこちら↓
 """
 st.write(markdown)
 st.write(df.groupby(['TEAM', 'CLASS', 'ビブスType', '背番号']).sum())

