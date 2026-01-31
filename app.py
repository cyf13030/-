import streamlit as st
import pandas as pd
import akshare as ak
import time
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="小倍养基 - 成长养基",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"  # 电脑强制展开侧边栏
)

# CSS - 使用 r""" 原始字符串，避免 px/em 报错
st.markdown(r"""
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

    .metrics { display: flex; flex-direction: column; gap: 12px; font-size: 1em; color: #555; }
    .metric-item { padding: 10px 0; border-top: 1px solid #eee; }
    .metric-label { font-weight: 500; color: #777; }

    button[kind="primary"], button {
        font-size: 1.2em !important;
        padding: 14px 24px !important;
        min-height: 54px !important;
        width: 100% !important;
        margin: 12px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="header-bar">小倍养基 - 成长养基</div>', unsafe_allow_html=True)

# 手机端引导
st.warning("📱 手机用户：点击左上角三横图标（☰）或从左侧向右滑动打开侧边栏 → 修改持仓份额/成本金额")

# 刷新按钮
if st.button("🔄 立即刷新数据", type="primary", use_container_width=True):
    st.rerun()

# 基金列表
fund_list = [
    {"代码": "110022", "名称": "易方达优选成长混合"},
    {"代码": "001593", "名称": "南方成份精选混合"},
    {"代码": "000001", "名称": "华夏成长混合"},
    {"代码": "519697", "名称": "长信量化先锋股票"},
]

# session_state
if 'holdings' not in st.session_state:
    st.session_state.holdings = {
        f["代码"]: {"份额": 0.0, "成本金额": 0.0}
        for f in fund_list
    }

# 侧边栏
with st.sidebar:
    st.header("持仓设置")
    
    selected_codes = st.multiselect(
        "显示的基金",
        options=[f["代码"] for f in fund_list],
        default=[f["代码"] for f in fund_list]
    )
    
    st.markdown("**修改持仓**")
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
    st.subheader("自动刷新")
    refresh_option = st.selectbox(
        "间隔",
        ["关闭", "每10秒", "每15秒", "每30秒", "每60秒"],
        index=1
    )

# 自动刷新
if refresh_option != "关闭":
    intervals = {"每10秒": 10, "每15秒": 15, "每30秒": 30, "每60秒": 60}
    time.sleep(intervals[refresh_option])
    st.rerun()

# 拉取实时估值
with st.spinner("正在获取东方财富实时估值..."):
    try:
        df_rt = ak.fund_value_estimation_em(symbol="全部")
        df_rt['基金代码'] = df_rt['基金代码'].astype(str).str.zfill(6)
        
        est_nav_col = next((c for c in df_rt.columns if '估算值' in c), None)
        est_growth_col = next((c for c in df_rt.columns if '估算增长率' in c), None)
        
        if not est_nav_col or not est_growth_col:
            st.warning("接口列名变化，无法识别估算值/增长率。请稍后再试。")
            df_rt = pd.DataFrame()
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
        df_rt = pd.DataFrame()

# 数据合并与计算
hold_df = pd.DataFrame([
    {'代码': code, '份额': info['份额'], '成本金额': info['成本金额']}
    for code, info in st.session_state.holdings.items()
    if code in selected_codes and info['份额'] > 0
])

if not hold_df.empty and not df_rt.empty:
    merged = hold_df.merge(df_rt, left_on='代码', right_on='基金代码', how='left')
    merged['名称'] = merged['代码'].map({f['代码']: f['名称'] for f in fund_list})
    
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
        <span class="{today_class}">今日收益 {total_today:+,.2f}</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span class="{cum_class}">累计收益 {total_cum:+,.2f}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**持仓明细**")

    for _, row in merged.iterrows():
        st.markdown(f"""
        <div class="holding-card">
            <div class="fund-name">{row['名称']}</div>
            <div class="amount">¥{row['估计金额']:,.2f}</div>
            <div class="metrics">
                <div class="metric-item">
                    <div class="metric-label">今日收益</div>
                    <div class="{'positive' if row['今日收益(元)'] >= 0 else 'negative'}">
                        {row['今日收益(元)']:+,.2f} ({row['日涨跌幅%']:+.2f}%)
                    </div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">累计收益</div>
                    <div class="{'positive' if row['累计收益(元)'] >= 0 else 'negative'}">
                        {row['累计收益(元)']:+,.2f} ({row['累计收益率(%)']:+.2f}%)
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("暂无持仓数据或估值未加载。请在侧边栏输入份额，或等待交易日。")

# 底部导航
st.markdown("""
<div class="bottom-nav">
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
        <span class="{today_class}">今日收益 {total_today:+,.2f}</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span class="{cum_class}">累计收益 {total_cum:+,.2f}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**持仓明细**")

    for _, row in merged.iterrows():
        st.markdown(f"""
        <div class="holding-card">
            <div class="fund-name">{row['名称']}</div>
            <div class="amount">¥{row['估计金额']:,.2f}</div>
            <div class="metrics">
                <div class="metric-item">
                    <div class="metric-label">今日收益</div>
                    <div class="{'positive' if row['今日收益(元)'] >= 0 else 'negative'}">
                        {row['今日收益(元)']:+,.2f} ({row['日涨跌幅%']:+.2f}%)
                    </div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">累计收益</div>
                    <div class="{'positive' if row['累计收益(元)'] >= 0 else 'negative'}">
                        {row['累计收益(元)']:+,.2f} ({row['累计收益率(%)']:+.2f}%)
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    import streamlit as st
import pandas as pd
import akshare as ak
import time
from datetime import datetime

# 页面配置：电脑强制展开侧边栏，手机折叠
st.set_page_config(
    page_title="小倍养基 - 成长养基",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"  # 电脑端直接看到侧边栏
)

# CSS - 使用 r""" 原始字符串，避免 Python 解析 px/em 报错
st.markdown(r"""
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

    .metrics { display: flex; flex-direction: column; gap: 12px; font-size: 1em; color: #555; }
    .metric-item { padding: 10px 0; border-top: 1px solid #eee; }
    .metric-label { font-weight: 500; color: #777; }

    button[kind="primary"], button {
        font-size: 1.2em !important;
        padding: 14px 24px !important;
        min-height: 54px !important;
        width: 100% !important;
        margin: 12px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="header-bar">小倍养基 - 成长养基</div>', unsafe_allow_html=True)

# 手机端最醒目引导（放在最上面）
st.warning("📱 手机用户：请点击左上角三横图标（☰）或从屏幕左侧向右滑动打开侧边栏 → 修改持仓份额/成本金额")

# 主页面常驻刷新按钮
if st.button("🔄 立即刷新数据", type="primary", use_container_width=True):
    st.rerun()

# 基金列表（可自行添加更多）
fund_list = [
    {"代码": "110022", "名称": "易方达优选成长混合"},
    {"代码": "001593", "名称": "南方成份精选混合"},
    {"代码": "000001", "名称": "华夏成长混合"},
    {"代码": "519697", "名称": "长信量化先锋股票"},
]

# session_state 保存持仓
if 'holdings' not in st.session_state:
    st.session_state.holdings = {
        f["代码"]: {"份额": 0.0, "成本金额": 0.0}
        for f in fund_list
    }

# 侧边栏（放在最后，确保前面语法无误）
with st.sidebar:
    st.header("持仓设置")
    
    selected_codes = st.multiselect(
        "显示的基金",
        options=[f["代码"] for f in fund_list],
        default=[f["代码"] for f in fund_list]
    )
    
    st.markdown("**修改持仓**")
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
    st.subheader("自动刷新")
    refresh_option = st.selectbox(
        "间隔",
        ["关闭", "每10秒", "每15秒", "每30秒", "每60秒"],
        index=1
    )

# 自动刷新
if refresh_option != "关闭":
    intervals = {"每10秒": 10, "每15秒": 15, "每30秒": 30, "每60秒": 60}
    time.sleep(intervals[refresh_option])
    st.rerun()

# 拉取实时估值
with st.spinner("正在获取东方财富实时估值..."):
    try:
        df_rt = ak.fund_value_estimation_em(symbol="全部")
        df_rt['基金代码'] = df_rt['基金代码'].astype(str).str.zfill(6)
        
        est_nav_col = next((c for c in df_rt.columns if '估算值' in c), None)
        est_growth_col = next((c for c in df_rt.columns if '估算增长率' in c), None)
        
        if not est_nav_col or not est_growth_col:
            st.warning("接口列名变化，无法识别估算值/增长率。请查看调试或稍后再试。")
            df_rt = pd.DataFrame()
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
        df_rt = pd.DataFrame()

# 数据合并与计算
hold_df = pd.DataFrame([
    {'代码': code, '份额': info['份额'], '成本金额': info['成本金额']}
    for code, info in st.session_state.holdings.items()
    if code in selected_codes and info['份额'] > 0
])

if not hold_df.empty and not df_rt.empty:
    merged = hold_df.merge(df_rt, left_on='代码', right_on='基金代码', how='left')
    merged['名称'] = merged['代码'].map({f['代码']: f['名称'] for f in fund_list})
    
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
        <span class="{today_class}">今日收益 {total_today:+,.2f}</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span class="{cum_class}">累计收益 {total_cum:+,.2f}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**持仓明细**")

    for _, row in merged.iterrows():
        st.markdown(f"""
        <div class="holding-card">
            <div class="fund-name">{row['名称']}</div>
            <div class="amount">¥{row['估计金额']:,.2f}</div>
            <div class="metrics">
                <div class="metric-item">
                    <div class="metric-label">今日收益</div>
                    <div class="{'positive' if row['今日收益(元)'] >= 0 else 'negative'}">
                        {row['今日收益(元)']:+,.2f} ({row['日涨跌幅%']:+.2f}%)
                    </div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">累计收益</div>
                    <div class="{'positive' if row['累计收益(元)'] >= 0 else 'negative'}">
                        {row['累计收益(元)']:+,.2f} ({row['累计收益率(%)']:+.2f}%)
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("暂无持仓数据或估值未加载。请在侧边栏输入份额，或等待交易日。")

# 底部导航
st.markdown("""
<div class="bottom-nav">
    <div class="nav-item">🏠 首页</div>
    <div class="nav-item">⭐ 自选</div>
    <div class="nav-item">🔍 发现</div>
    <div class="nav-item">📈 行情</div>
    <div class="nav-item">👤 我的</div>
</div>
""", unsafe_allow_html=True)
