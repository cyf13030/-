# app.py - 小倍养基 - 完整实时持仓仪表盘（2026年1月版）
import streamlit as st
import pandas as pd
import akshare as ak
import time
from datetime import datetime

# ────────────────────────────────────────────────
# 页面配置 & CSS（支付宝/微信养基风格）
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="小倍养基 - 账户总览",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #fff8e1 0%, #fffde7 100%);
        font-family: -apple-system, BlinkMacOSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header, #MainMenu, footer { visibility: hidden; }

    .header-bar {
        background: linear-gradient(90deg, #ffca28, #ffb300);
        padding: 16px 20px;
        border-radius: 0 0 20px 20px;
        color: #333;
        font-weight: bold;
        text-align: center;
        margin: -16px -16px 24px -16px;
    }

    .big-number {
        font-size: 48px;
        font-weight: bold;
        color: #1a1a1a;
        text-align: center;
        margin: 0 0 8px 0;
    }

    .gain-box {
        font-size: 22px;
        text-align: center;
        margin-bottom: 24px;
    }

    .positive { color: #4caf50; }
    .negative { color: #f44336; }

    .holding-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .fund-name {
        font-size: 17px;
        font-weight: 600;
        color: #333;
        margin-bottom: 8px;
    }

    .amount {
        font-size: 22px;
        font-weight: bold;
        color: #000;
        margin-bottom: 12px;
    }

    .metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        font-size: 14px;
        color: #555;
    }

    .metric-item {
        flex: 1 1 45%;
        min-width: 140px;
    }

    .metric-label {
        font-weight: 500;
        color: #777;
    }

    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 1px solid #eee;
        padding: 10px 0;
        display: flex;
        justify-content: space-around;
        font-size: 12px;
        color: #666;
        z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }

    .nav-item { text-align: center; }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="header-bar">小倍养基 - 成长养基</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 持仓数据（可替换为你的真实持仓列表）
# ────────────────────────────────────────────────
initial_data = {
    '代码': ['110022', '001593', '000001', '519697', '000698'],
    '名称': [
        '易方达优选成长混合',
        '南方成份精选混合',
        '华夏成长混合',
        '长信量化先锋股票',
        '金信精选成长混合C'
    ]
}
df_base = pd.DataFrame(initial_data)

# session_state 保存份额和成本金额
if 'holdings' not in st.session_state:
    st.session_state.holdings = {
        code: {'份额': 0.0, '成本金额': 0.0}
        for code in df_base['代码']
    }

# ────────────────────────────────────────────────
# 侧边栏：持仓管理 + 自动刷新设置
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("持仓管理")
    
    selected_codes = st.multiselect(
        "显示的基金",
        options=df_base['代码'].tolist(),
        default=df_base['代码'].tolist(),
        key="selected_codes"
    )
    
    st.markdown("**修改份额 & 成本金额**")
    for code in selected_codes:
        info = st.session_state.holdings[code]
        share = st.number_input(
            f"{code} 份额",
            min_value=0.0,
            value=info['份额'],
            step=100.0,
            format="%.2f",
            key=f"share_{code}"
        )
        cost = st.number_input(
            f"{code} 成本金额 (元)",
            min_value=0.0,
            value=info['成本金额'],
            step=1000.0,
            format="%.2f",
            key=f"cost_{code}"
        )
        st.session_state.holdings[code]['份额'] = share
        st.session_state.holdings[code]['成本金额'] = cost
    
    st.markdown("---")
    st.subheader("数据刷新")
    refresh_option = st.selectbox(
        "自动刷新间隔",
        ["关闭", "每10秒", "每15秒", "每30秒", "每60秒"],
        index=1,
        help="自动拉取东方财富最新估值"
    )

# ────────────────────────────────────────────────
# 自动刷新逻辑
# ────────────────────────────────────────────────
if refresh_option != "关闭":
    intervals = {"每10秒": 10, "每15秒": 15, "每30秒": 30, "每60秒": 60}
    time.sleep(intervals[refresh_option])
    st.rerun()

# ────────────────────────────────────────────────
# 拉取实时估值数据
# ────────────────────────────────────────────────
with st.spinner("正在拉取东方财富实时估值..."):
    try:
        df_rt = ak.fund_value_estimation_em(symbol="全部")
        df_rt['基金代码'] = df_rt['基金代码'].astype(str).str.zfill(6)
        df_rt = df_rt[df_rt['基金代码'].isin(selected_codes)]
        
        # 处理列名（可能带日期前缀）
        est_nav_col = next((c for c in df_rt.columns if '估算值' in c), None)
        est_growth_col = next((c for c in df_rt.columns if '估算增长率' in c), None)
        
        if not est_nav_col or not est_growth_col:
            st.error("接口列名变化，无法识别估算值/增长率列。请查看调试信息或稍后再试。")
            st.stop()
        
        df_rt = df_rt[['基金代码', est_nav_col, est_growth_col]]
        df_rt = df_rt.rename(columns={
            est_nav_col: '估算净值',
            est_growth_col: '日涨跌幅%'
        })
        
        df_rt['估算净值'] = pd.to_numeric(df_rt['估算净值'], errors='coerce')
        df_rt['日涨跌幅%'] = pd.to_numeric(df_rt['日涨跌幅%'].astype(str).str.rstrip('%'), errors='coerce')
        
        # 调试列名（可删除）
        st.caption("当前接口列名（调试用）")
        st.code(", ".join(df_rt.columns.tolist()))
        
    except Exception as e:
        st.error(f"拉取实时数据失败：{str(e)}")
        st.info("建议：pip install akshare --upgrade 或检查网络/是否交易日")
        st.stop()

# ────────────────────────────────────────────────
# 数据合并与计算
# ────────────────────────────────────────────────
current_hold = pd.DataFrame([
    {'代码': code, '份额': info['份额'], '成本金额': info['成本金额']}
    for code, info in st.session_state.holdings.items()
    if code in selected_codes
])

merged = current_hold.merge(df_rt, left_on='代码', right_on='基金代码', how='left')
merged = merged.drop(columns=['基金代码'], errors='ignore')

# 名称映射
name_map = dict(zip(df_base['代码'], df_base['名称']))
merged['名称'] = merged['代码'].map(name_map)

# 计算收益
merged['估计金额'] = merged['份额'] * merged['估算净值']
merged['今日收益(元)'] = merged['估计金额'] * (merged['日涨跌幅%'] / 100)
merged['累计收益(元)'] = merged['估计金额'] - merged['成本金额']
merged['累计收益率(%)'] = ((merged['估计金额'] - merged['成本金额']) / merged['成本金额'].replace(0, float('nan'))) * 100

# 汇总
total_assets = merged['估计金额'].sum()
total_today_gain = merged['今日收益(元)'].sum()
total_cum_gain = merged['累计收益(元)'].sum()

# ────────────────────────────────────────────────
# 显示总览
# ────────────────────────────────────────────────
st.markdown(f'<div class="big-number">{total_assets:,.2f}</div>', unsafe_allow_html=True)

today_class = "positive" if total_today_gain >= 0 else "negative"
c
