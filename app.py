import streamlit as st

st.set_page_config(page_title="侧边栏测试", layout="wide")

st.title("测试页面 - 电脑端侧边栏是否显示")

st.info("如果左侧看到侧边栏内容，说明侧边栏机制正常")

with st.sidebar:
    st.header("侧边栏测试区")
    st.write("这是侧边栏内容")
    st.button("测试按钮")
    st.slider("测试滑块", 0, 100)
    st.text_input("输入框测试")

st.write("主页面内容在这里。如果侧边栏显示了，问题出在原代码逻辑。")
