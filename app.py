import streamlit as st

st.set_page_config(
    page_title="侧边栏测试",
    layout="wide",
    initial_sidebar_state="expanded"  # 电脑强制展开
)

st.title("测试：侧边栏是否出现")

st.warning("如果左侧看到侧边栏 → 说明侧边栏机制正常。问题出在原代码")

with st.sidebar:
    st.header("侧边栏测试区")
    st.markdown("这是侧边栏内容")
    st.button("测试按钮")
    st.slider("测试滑块", 0, 100)
    st.text_input("输入测试")

st.info("主页面内容。如果侧边栏显示了，请告诉我结果，我再给你修复完整版")
