# app.py - 基金估值小工具（语法安全重构版 - 2026年1月）
import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="基金估值小工具",
    page_icon="📈",
    layout="wide"
)

st.title("个人基金估值查询（含估计金额）")
st.caption(
    f"数据来源：东方财富估算净值 via AKShare | "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

DEFAULT_FUNDS = [
    "110022",
    "001593",
    "000001",
    "519697",
]

if 'fund_shares' not in st.session_state:
    st.session_state.fund_shares = {}

with st.sidebar:
    st.header("基金选择 & 持有份额")
    
    selected_funds = st.multiselect(
        "选择关注的基金",
        options=DEFAULT_FUNDS + ["其他"],
        default=DEFAULT_FUNDS[:3]
    )
    
    custom_input = st.text_input(
        "手动输入基金代码（逗号分隔）",
        placeholder="例如：161725,005827,159941"
    )
    
    if custom_input:
        extras = [
            c.strip()
            for c in custom_input.split(",")
            if c.strip().isdigit() and len(c.strip()) == 6
        ]
        selected_funds = list(set(selected_funds + extras))
    
    st.markdown("**输入持有份额（份）**")
    
    for fund in selected_funds:
        default_share = st.session_state.fund_shares.get(fund, 0.0)
        share = st.number_input(
            label=f"{fund} 份额",
            min_value=0.0,
            value=default_share,
            step=100.0,
            format="%.2f",
            key=f"share_{fund}"
        )
        st.session_state.fund_shares[fund] = share
    
    st.button("🔄 刷新数据", type="primary")

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
