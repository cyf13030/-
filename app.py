import streamlit as st
import pandas as pd
import time
from datetime import datetime

# ────────────────────────────────────────────────
# 页面配置 & 自定义 CSS（支付宝/微信养基风格）
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="小倍养基 - 实时持仓",
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

# ────────────────────────────────────────────────
# 标题 & 头部
# ────────────────────────────────────────────────
st.markdown('<div class="header-bar">小倍养基 - 成长养基</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 持仓数据（可修改为你的真实持仓）
# ────────────────────────────────────────────────
initial_data = {
    '代码': ['000698', '159941', '005827', '110022'],
    '名称': ['金信精选成长混合C', '广发纳指100ETF联接C', '银河创新混合C', '易方达优选成长混合'],
    '份额': [10000.0, 2000.0, 6000.0, 5000.0],
    '成本金额': [105000.0, 11800.0, 58000.0, 48000.0]
}
df_base = pd.DataFrame(initial_data)

# session_state 保存用户修改后的份额和成本
if 'holdings' not in st.session_state:
    st.session_state.holdings = df_base.set_index('代码')[['份额', '成本金额']].to_dict(orient='index')

# ────────────────────────────────────────────────
# 侧边栏：管理持仓 + 自动刷新设置
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("持仓设置")
    
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
    st.subheader("自动刷新")
    refresh_option = st.selectbox(
        "刷新间隔",
        ["关闭", "每10秒", "每15秒", "每30秒", "每60秒"],
        index=1,
        help="自动拉取最新估值数据"
    )

# ────────────────────────────────────────────────
# 自动刷新逻辑
# ────────────────────────────────────────────────
if refresh_option != "关闭":
    intervals = {"每10秒": 10, "每15秒": 15, "每30秒": 30, "每60秒": 60}
    time.sleep(intervals[refresh_option])
    st.rerun()

# ────────────────────────────────────────────────
# 模拟实时估值数据（实际请替换为 akshare 接口）
# ────────────────────────────────────────────────
simulated_data = {
    '代码': ['000698', '159941', '005827', '110022'],
    '估算净值': [1.8563, 7.3177, 9.9780, 2.1500],
    '日涨跌幅%': [-0.68, -0.53, 1.95, 0.45]
}
df_rt = pd.DataFrame(simulated_data)

# ────────────────────────────────────────────────
# 数据合并与计算
# ────────────────────────────────────────────────
current_hold = pd.DataFrame([
    {'代码': code, '份额': info['份额'], '成本金额': info['成本金额']}
    for code, info in st.session_state.holdings.items()
    if code in selected_codes
])

merged = current_hold.merge(df_rt, on='代码', how='left')

merged['估算净值'] = pd.to_numeric(merged['估算净值'], errors='coerce')
merged['日涨跌幅%'] = pd.to_numeric(merged['日涨跌幅%'], errors='coerce')

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
cum_class = "positive" if total_cum_gain >= 0 else "negative"

st.markdown(f"""
<div class="gain-box">
    <span class="{today_class}">今日 {total_today_gain:+,.2f}</span>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <span class="{cum_class}">累计 {total_cum_gain:+,.2f}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("**持仓明细**")

for _, row in merged.iterrows():
    name = [n for c, n in zip(df_base['代码'], df_base['名称']) if c == row['代码']][0]
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
      if not selected_funds:
    st.info("请至少选择或输入一个基金代码")
else:
    with st.spinner("正在拉取估值数据..."):
        try:
            df = ak.fund_value_estimation_em(symbol="全部")
            df['基金代码'] = df['基金代码'].astype(str).str.zfill(6)
            
            st.caption("调试：当前接口返回的列名")
            st.code(", ".join(df.columns.tolist()))
            
            value_col = next((c for c in df.columns if '估算值' in c), None)
            growth_col = next((c for c in df.columns if '估算增长率' in c), None)
            bias_col = next((c for c in df.columns if '偏差' in c), None)
            
            if not value_col or not growth_col:
                st.error("列名匹配失败。请把上方列名列表复制给我。")
            else:
                cols = ['基金代码', '基金名称', value_col, growth_col]
                if bias_col:
                    cols.append(bias_col)
                
                watched = df[df['基金代码'].isin(selected_funds)][cols].copy()
                
                watched = watched.rename(columns={
                    '基金代码': '代码',
                    '基金名称': '名称',
                    value_col: '估算净值',
                    growth_col: '估算涨幅',
                })
                if bias_col:
                    watched = watched.rename(columns={bias_col: '偏差'})
                
                watched['估算净值'] = pd.to_numeric(
                    watched['估算净值'].astype(str).str.replace(',', '').str.strip().replace(['', '--'], float('nan')),
                    errors='coerce'
                )
                
                watched['估算涨幅(%)'] = pd.to_numeric(
                    watched['估算涨幅'].astype(str).str.replace('%', '').str.strip().replace(['', '--'], '0'),
                    errors='coerce'
                ).fillna(0)
                
                if '偏差' in watched.columns:
                    watched['偏差'] = pd.to_numeric(
                        watched['偏差'].astype(str).str.replace('%', '').str.strip().replace(['', '--'], '0'),
                        errors='coerce'
                    ).fillna(0)
                
                watched['估计金额'] = 0.0
                for idx, row in watched.iterrows():
                    code = row['代码']
                    nav = row['估算净值']
                    shares = st.session_state.fund_shares.get(code, 0.0)
                    if pd.notna(nav) and shares > 0:
                        watched.at[idx, '估计金额'] = nav * shares
                
                watched = watched.sort_values('估算涨幅(%)', ascending=False).reset_index(drop=True)
                
                def fmt_float(x):
                    return "—" if pd.isna(x) else f"{x:.4f}"
                
                def fmt_pct(x):
                    return "—" if pd.isna(x) else f"{x:+.2f}%"
                
                def fmt_money(x):
                    return "—" if x <= 0 else f"{x:,.2f}"
                
                st.subheader(f"估值快照（{len(watched)} 只）")
                st.dataframe(
                    watched.style.format({
                        '估算净值': fmt_float,
                        '估算涨幅(%)': fmt_pct,
                        '偏差': fmt_pct if '偏差' in watched.columns else None,
                        '估计金额': fmt_money
                    }).background_gradient(
                        subset=['估算涨幅(%)'],
                        cmap='RdYlGn',
                        vmin=-5,
                        vmax=5
                    ),
                    use_container_width=True
                )
                
                total = watched['估计金额'].sum()
                if total > 0:
                    st.success(f"估算总金额 ≈ {total:,.2f} 元")
                
                st.subheader("涨幅对比")
                st.bar_chart(
                    watched.set_index('名称')['估算涨幅(%)'].fillna(0),
                    height=400
                )
        
        except Exception as e:
            st.error(f"发生错误：{str(e)}")
            st.info("建议：pip install akshare --upgrade 或检查网络/交易日")

st.markdown("---")
st.caption("数据仅供参考 | 金额基于用户输入的份额估算")
