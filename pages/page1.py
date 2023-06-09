import streamlit as st
import pandas as pd

st.title('ランニングスコア')
st.header('ヘッダを表示')
st.subheader('サブヘッダを表示')
st.caption('キャプションを表示')

df = pd.DataFrame(
    [
       {"command": "st.selectbox", "rating": 4, "is_widget": True, "is_widget2": True},
       {"command": "st.balloons", "rating": 5, "is_widget": False, "is_widget2": True},
       {"command": "st.time_input", "rating": 3, "is_widget": True, "is_widget2": True},
   ]
)
edited_df = st.experimental_data_editor(df, num_rows="dynamic")

favorite_command = edited_df.loc[edited_df["rating"].idxmax()]["command"]
st.markdown(f"Your favorite command is **{favorite_command}** ?")


df = pd.DataFrame(
    [
       {"command1": "st.selectbox", "rating1": 4, "is_widget3": True, "is_widget5": True},
       {"command1": "st.balloons", "rating1": 5, "is_widget3": False, "is_widget5": True},
       {"command1": "st.time_input", "rating1": 3, "is_widget3": True, "is_widget5": True},
   ]
)
edited_df = st.experimental_data_editor(df, num_rows="dynamic")




check = st.checkbox("check button") # チェックボタン

if check:
  st.button("button")
  st.selectbox("selectbox", ("select1", "select2"))
  st.multiselect("multiselectbox", ("select1", "select2"))
  st.radio("radiobutton", ("radio1", "radio2"))
  st.text_input("text input")
  st.text_area("text area")
  st.slider("slider", 0, 100, 50)
  st.file_uploader("Choose file")
  
  
st.button("button")
st.selectbox("selectbox", ("select1", "select2"))
st.multiselect("multiselectbox", ("select1", "select2"))
st.radio("radiobutton", ("radio1", "radio2"))
# 以下をサイドバーに表示
st.sidebar.text_input("text input")
st.sidebar.text_area("text area")
st.sidebar.slider("slider", 0, 100, 50)
st.sidebar.file_uploader("Choose file")

markdown = """
### st.writeでデータフレームを表形式で表示できます！
以下のコードでpandasのデータフレームをそのまま表にすることが可能です。
```python
st.write(df.head(7))
```
結果はこちら↓
"""
st.write(markdown)