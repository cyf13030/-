import streamlit as st
import pandas as pd
import akshare as ak
import time
from datetime import datetime

# 页面配置：电脑端强制展开侧边栏，手机端默认折叠但有引导
st.set_page_config(
    page_title="小倍养基 - 成长养基",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"  # 电脑端默认展开
)

# CSS 优化（手机按钮更大、间距更好）
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
        font-size: 1.5em;
    }

    .big-number {
        font-size: 3.5em;
        font-weight: bold;
        text-align: center;
        margin: 0 0 8px;
        color: #1a1a1a;
    }

    .gain-box {
        font-size: 1.5em;
        text-align: center;
        margin: 0 0 24px;
    }

    .positive { color: #4caf50; }
    .negative { color: #f44336; }

    .holding-card {
        background: white;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }

    .fund-name { font-size: 1.2em; font-weight: 600; color: #333; margin-bottom: 10px; }
    .amount { font-size: 1.8em; font-weight: bold; color: #000; margin-bottom: 12px; }

    .metrics {
        display: flex;
        flex-direction: column;
        gap: 12px;
        font-size: 1em;
        color: #555;
    }

    .metric-item { padding: 10px 0; border-top: 1px solid #eee; }

    button[kind="primary"], button {
        font-size: 1.2em !important;
        padding: 14px 24px !important;
        min-height: 54px !important;
        width: 100% !important;
        margin: 12px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 头部
st.markdown('<div class="header-bar">小倍养基 - 成长养基</div>', unsafe_allow_html=True)

# 手机端常驻引导（最醒目位置）
st.warning("""
📱 手机用户：请点击左上角三横图标（☰）或从屏幕左侧向右滑动打开侧边栏  
→ 在侧边栏修改持仓份额/成本金额 → 返回后点击“立即刷新”
""")

# 主页面常驻刷新按钮
col1, col2 = st.columns([3, 1])
with col1:
    st.title("持仓总览")
with col2:
    if st.button("🔄 立即刷新", type="primary", use_container_width=True):
        st.rerun()

# ────────────────────────────────────────────────
# 基金列表（可扩展）
# ────────────────────────────────────────────────
funds = [
    {"代码": "110022", "名称": "易方达优选成长混合"},
    {"代码": "001593", "名称": "南方成份精选混合"},
    {"代码": "000001", "名称": "华夏成长混合"},
    {"代码": "519697", "名称": "长信量化先锋股票"},
]

# session_state 保存持仓
if 'holdings' not in st.session_state:
    st.session_state.holdings = {f["代码"]: {"份额": 0.0, "成本金额": 0.0} for f in funds}

# ────────────────────────────────────────────────
# 侧边栏（只放高级设置）
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("持仓设置")
    
    selected_codes = st.multiselect(
        "显示基金",
        options=[f["代码"] for f in funds],
        default=[f["代码"] for f in funds]
    )
    
    for code in selected_codes:
        info = st.session_state.holdings[code]
        st.number_input(f"{code} 份额", value=info['份额'], step=100.0, key=f"share_{code}")
        st.number_input(f"{code} 成本金额", value=info['成本金额'], step=1000.0, key=f"cost_{code}")

    st.subheader("自动刷新")
    refresh_choice = st.selectbox("间隔", ["关闭", "每10秒", "每15秒", "每30秒"], index=0)

if refresh_choice != "关闭":
    interval = {"每10秒": 10, "每15秒": 15, "每30秒": 30}[refresh_choice]
    time.sleep(interval)
    st.rerun()

# ────────────────────────────────────────────────
# 拉取实时数据
# ────────────────────────────────────────────────
with st.spinner("获取实时估值..."):
    try:
        df_rt = ak.fund_value_estimation_em("全部")
        df_rt['基金代码'] = df_rt['基金代码'].astype(str).str.zfill(6)
        
        est_nav = next((c for c in df_rt.columns if '估算值' in c), None)
        est_growth = next((c for c in df_rt.columns if '估算增长率' in c), None)
        
        if est_nav and est_growth:
            df_rt = df_rt[['基金代码', est_nav, est_growth]]
            df_rt = df_rt.rename(columns={est_nav: '估算净值', est_growth: '日涨跌幅%'})
            df_rt['估算净值'] = pd.to_numeric(df_rt['估算净值'], errors='coerce')
            df_rt['日涨跌幅%'] = pd.to_numeric(df_rt['日涨跌幅%'].astype(str).str.rstrip('%'), errors='coerce')
        else:
            df_rt = pd.DataFrame()
    except:
        df_rt = pd.DataFrame()

# ────────────────────────────────────────────────
# 计算并显示
# ────────────────────────────────────────────────
hold_df = pd.DataFrame([
    {'代码': code, '份额': d['份额'], '成本金额': d['成本金额']}
    for code, d in st.session_state.holdings.items()
    if code in selected_codes and d['份额'] > 0
])

if not hold_df.empty and not df_rt.empty:
    merged = hold_df.merge(df_rt, left_on='代码', right_on='基金代码', how='left')
    merged['名称'] = merged['代码'].map({f['代码']: f['名称'] for f in funds})
    
    merged['估计金额'] = merged['份额'] * merged['估算净值']
    merged['今日收益(元)'] = merged['估计金额'] * (merged['日涨跌幅%'] / 100)
    merged['累计收益(元)'] = merged['估计金额'] - merged['成本金额']
    merged['累计收益率(%)'] = ((merged['估计金额'] - merged['成本金额']) / merged['成本金额'].replace(0, float('nan'))) * 100

    total_assets = merged['估计金额'].sum()
    total_today = merged['今日收益(元)'].sum()
    total_cum = merged['累计收益(元)'].sum()

    st.markdown(f'<div class="big-number">{total_assets:,.2f}</div>', unsafe_allow_html=True)

    today_class = "positive" if total_today >= 0 else "negative"
    cum_class = "positive" if total_cum >= 0 else "negative"

    st.markdown(f"""
    <div class="gain-box">
        <span class="{today_class}">今日 {total_today:+,.2f}</span> |
        <span class="{cum_class}">累计 {total_cum:+,.2f}</span>
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
    st.info("暂无持仓或数据未加载。请在侧边栏输入份额，或等待交易日。")

# 底部导航
# 替换原来的多行 f-string
st.markdown(
    '<div class="holding-card">'
    f'<div class="fund-name">{row["名称"]}</div>'
    f'<div class="amount">¥{row["估计金额"]:,.2f}</div>'
    '<div class="metrics">'
    f'<div class="metric-item">'
    '  <div class="metric-label">今日收益</div>'
    f'  <div class="{today_class}">{today_gain:+,.2f} ({row["日涨跌幅%"]:+.2f}%)</div>'
    '</div>'
    f'<div class="metric-item">'
    '  <div class="metric-label">累计收益</div>'
    f'  <div class="{cum_class}">{cum_gain:+,.2f} ({cum_pct:+.2f}%)</div>'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)
