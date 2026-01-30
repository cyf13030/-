# app.py - 小倍养基 - 移动端优化完整版（2026年1月）
import streamlit as st
import pandas as pd
import akshare as ak
import time
from datetime import datetime, time as dt_time

st.set_page_config(
    page_title="小倍养基 - 成长养基",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"  # 手机默认折叠侧边栏
)

# ────────────────────────────────────────────────
# CSS（手机端优化：按钮更大、文字更清晰、间距适中）
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fff8e1 0%, #fffde7 100%); }
    header, #MainMenu, footer { visibility: hidden; }

    .header-bar {
        background: linear-gradient(90deg, #ffca28, #ffb300);
        padding: 18px 20px;
        border-radius: 0 0 24px 24px;
        color: #333;
        font-weight: bold;
        text-align: center;
        margin: -16px -16px 24px -16px;
        font-size: 1.4em;
    }

    .big-number {
        font-size: 3.2em;
        font-weight: bold;
        text-align: center;
        margin: 0 0 8px;
        color: #1a1a1a;
    }

    .gain-box {
        font-size: 1.4em;
        text-align: center;
        margin: 0 0 20px;
    }

    .positive { color: #4caf50; }
    .negative { color: #f44336; }

    .holding-card {
        background: white;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }

    .fund-name {
        font-size: 1.15em;
        font-weight: 600;
        color: #333;
        margin-bottom: 8px;
    }

    .amount {
        font-size: 1.6em;
        font-weight: bold;
        color: #000;
        margin-bottom: 12px;
    }

    .metrics {
        display: flex;
        flex-direction: column;
        gap: 10px;
        font-size: 0.95em;
        color: #555;
    }

    .metric-item {
        padding: 8px 0;
        border-top: 1px solid #eee;
    }

    .metric-label {
        font-weight: 500;
        color: #777;
    }

    /* 手机端按钮更大 */
    button[kind="primary"], button {
        font-size: 1.1em !important;
        padding: 14px 24px !important;
        min-height: 52px !important;
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
        font-size: 0.85em;
        color: #666;
        z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="header-bar">小倍养基 - 成长养基</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 持仓基础数据（可替换为你的真实基金）
# ────────────────────────────────────────────────
fund_list = [
    {"代码": "110022", "名称": "易方达优选成长混合"},
    {"代码": "001593", "名称": "南方成份精选混合"},
    {"代码": "000001", "名称": "华夏成长混合"},
    {"代码": "519697", "名称": "长信量化先锋股票"},
    {"代码": "000698", "名称": "金信精选成长混合C"},
]

# session_state 保存份额和成本
if 'holdings' not in st.session_state:
    st.session_state.holdings = {
        f["代码"]: {"份额": 0.0, "成本金额": 0.0}
        for f in fund_list
    }

# ────────────────────────────────────────────────
# 主页面 - 常用操作放主区域（手机友好）
# ────────────────────────────────────────────────
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.title("持仓总览")
with col_refresh:
    if st.button("🔄 刷新", type="primary", use_container_width=True):
        st.rerun()

# 手机端引导提示（非常重要）
st.info("📱 手机用户：点击左上角三横图标可打开侧边栏 → 修改持仓份额/成本金额")

# ────────────────────────────────────────────────
# 拉取实时估值
# ────────────────────────────────────────────────
with st.spinner("正在获取东方财富实时估值..."):
    try:
        df_rt = ak.fund_value_estimation_em(symbol="全部")
        df_rt['基金代码'] = df_rt['基金代码'].astype(str).str.zfill(6)

        est_nav_col = next((c for c in df_rt.columns if '估算值' in c), None)
        est_growth_col = next((c for c in df_rt.columns if '估算增长率' in c), None)

        if not est_nav_col or not est_growth_col:
            st.warning("接口列名可能变化，请查看调试信息或稍后再试")
        else:
            df_rt = df_rt[['基金代码', est_nav_col, est_growth_col]]
            df_rt = df_rt.rename(columns={
                est_nav_col: '估算净值',
                est_growth_col: '日涨跌幅%'
            })
            df_rt['估算净值'] = pd.to_numeric(df_rt['估算净值'], errors='coerce')
            df_rt['日涨跌幅%'] = pd.to_numeric(df_rt['日涨跌幅%'].astype(str).str.rstrip('%'), errors='coerce')
    except Exception as e:
        st.error(f"数据拉取失败：{str(e)}")
        df_rt = pd.DataFrame()  # 空表

# ────────────────────────────────────────────────
# 合并计算
# ────────────────────────────────────────────────
current_hold = pd.DataFrame([
    {'代码': code, '份额': info['份额'], '成本金额': info['成本金额']}
    for code, info in st.session_state.holdings.items()
    if info['份额'] > 0
])

if not current_hold.empty and not df_rt.empty:
    merged = current_hold.merge(df_rt, left_on='代码', right_on='基金代码', how='left')
    merged['名称'] = merged['代码'].map({f['代码']: f['名称'] for f in fund_list})
    merged['估计金额'] = merged['份额'] * merged['估算净值']
    merged['今日收益(元)'] = merged['估计金额'] * (merged['日涨跌幅%'] / 100)
    merged['累计收益(元)'] = merged['估计金额'] - merged['成本金额']
    merged['累计收益率(%)'] = ((merged['估计金额'] - merged['成本金额']) / merged['成本金额'].replace(0, float('nan'))) * 100

    total_assets = merged['估计金额'].sum()
    total_today = merged['今日收益(元)'].sum()
    total_cum = merged['累计收益(元)'].sum()

    # 显示总览
    st.markdown(f'<div class="big-number">{total_assets:,.2f}</div>', unsafe_allow_html=True)

    today_class = "positive" if total_today >= 0 else "negative"
    cum_class = "positive" if total_cum >= 0 else "negative"

    st.markdown(f"""
    <div class="gain-box">
        <span class="{today_class}">今日收益 {total_today:+,.2f}</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span class="{cum_class}">累计收益 {total_cum:+,.2f}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**持仓明细**")

    for _, row in merged.iterrows():
        name = row['名称']
        amount = row['估计金额']
        today_gain = row['今日收益(元)']
        cum_gain = row['累计收益(元)']
        cum_pct = row['累计收益率(%)']

        today_class = "positive" if today_gain >= 0 else "negative"
        cum_class = "positive" if cum_gain >= 0 else "negative"

        st.markdown(f"""
        <div class="holding-card">
            <div class="fund-name">{name}</div>
            <div class="amount">¥{amount:,.2f}</div>
            <div class="metrics">
                <div class="metric-item">
                    <div class="metric-label">今日收益</div>
                    <div class="{today_class}">{today_gain:+,.2f} ({row['日涨跌幅%']:+.2f}%)</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">累计收益</div>
                    <div class="{cum_class}">{cum_gain:+,.2f} ({cum_pct:+.2f}%)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("暂无持仓数据或实时估值拉取失败。请在侧边栏添加份额，或检查网络。")
