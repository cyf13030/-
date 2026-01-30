# app.py - 个人基金估值小工具（修复所有已知错误版）
import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="基金估值小工具", page_icon="📈", layout="wide")

st.title("个人基金估值查询")
st.caption(f"数据来源：东方财富估算净值 via AKShare | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

DEFAULT_FUNDS = [
    "110022",  # 易方达优选成长混合
    "001593",  # 南方成份精选混合
    "000001",  # 华夏成长混合
    "519697",  # 长信量化先锋股票
    # 添加更多你的基金代码
]

with st.sidebar:
    st.header("基金选择")
    selected_funds = st.multiselect(
        "选择关注的基金",
        options=DEFAULT_FUNDS + ["其他"],
        default=DEFAULT_FUNDS[:3],
        help="可多选"
    )
    
    custom_input = st.text_input(
        "手动输入基金代码（多个用逗号分隔）",
        placeholder="例如：161725,005827,159941"
    )
    if custom_input:
        extras = [c.strip() for c in custom_input.split(",") if c.strip().isdigit() and len(c.strip()) == 6]
        selected_funds = list(set(selected_funds + extras))
    
    if st.button("🔄 刷新数据", type="primary"):
        st.rerun()

if not selected_funds:
    st.info("请至少选择或输入一个基金代码")
else:
    with st.spinner("正在拉取东方财富估算数据..."):
        try:
            df = ak.fund_value_estimation_em(symbol="全部")
            df['基金代码'] = df['基金代码'].astype(str).str.zfill(6)
            
            # 调试：显示实际列名
            st.caption("调试：AKShare 当前返回的列名（用于排查）")
            st.code(", ".join(df.columns.tolist()), language="text")
            
            # 动态匹配列名（兼容旧版和新版）
            value_col_candidates = ["交易日-估算数据-估算值", "估算值", "实时估算值", "估算净值"]
            growth_col_candidates = ["交易日-估算数据-估算增长率", "估算增长率", "增长率估算"]
            bias_col_candidates = ["估算偏差", "偏差", "估算偏离"]
            
            value_col = next((c for c in df.columns if c in value_col_candidates), None)
            growth_col = next((c for c in df.columns if c in growth_col_candidates), None)
            bias_col = next((c for c in df.columns if c in bias_col_candidates), None)
            
            if not value_col or not growth_col:
                st.error("无法找到估算值或增长率列。请查看上方列名列表，并告诉我，我帮你进一步调整。")
            else:
                cols = ['基金代码', '基金名称', value_col, growth_col]
                if bias_col:
                    cols.append(bias_col)
                
                watched = df[df['基金代码'].isin(selected_funds)][cols].copy()
                
                # 重命名
                rename_map = {
                    '基金代码': '代码',
                    '基金名称': '名称',
                    value_col: '估算净值',
                    growth_col: '估算涨幅'
                }
                if bias_col:
                    rename_map[bias_col] = '偏差'
                watched = watched.rename(columns=rename_map)
                
                # 清洗 & 转数值
                watched['估算净值'] = (
                    watched['估算净值'].astype(str)
                    .str.replace(',', '', regex=False)
                    .str.strip()
                    .replace(['', '--', '暂无数据', '无'], float('nan'))
                )
                watched['估算净值'] = pd.to_numeric(watched['估算净值'], errors='coerce')
                
                watched['估算涨幅(%)'] = (
                    watched['估算涨幅'].astype(str)
                    .str.replace('%', '', regex=False)
                    .str.strip()
                    .replace(['', '--', '暂无'], '0')
                )
                watched['估算涨幅(%)'] = pd.to_numeric(watched['估算涨幅(%)'], errors='coerce').fillna(0)
                
                if '偏差' in watched.columns:
                    watched['偏差'] = (
                        watched['偏差'].astype(str)
                        .str.replace('%', '', regex=False)
                        .str.strip()
                        .replace(['', '--'], '0')
                    )
                    watched['偏差'] = pd.to_numeric(watched['偏差'], errors='coerce').fillna(0)
                
                watched = watched.sort_values('估算涨幅(%)', ascending=False).reset_index(drop=True)
                
                # 安全格式化函数
                def safe_float_format(val, decimals=4):
                    if pd.isna(val):
                        return "—"
                    return f"{val:.{decimals}f}"
                
                def safe_pct_format(val):
                    if pd.isna(val):
                        return "—"
                    return f"{val:+.2f}%"
                
                # 表格样式
                st.subheader(f"估值快照（找到 {len(watched)} 只）")
                styled_df = watched.style.format({
                    '估算净值': lambda x: safe_float_format(x, 4),
                    '估算涨幅(%)': safe_pct_format,
                    '偏差': lambda x: safe_pct_format(x) if '偏差' in watched.columns else None
                }).background_gradient(
                    subset=['估算涨幅(%)'],
                    cmap='RdYlGn',
                    vmin=-5,
                    vmax=5
                )
                
                st.dataframe(styled_df, use_container_width=True)
                
                # 图表
                st.subheader("估算涨幅对比")
                chart_data = watched.set_index('名称')['估算涨幅(%)'].fillna(0)
                st.bar_chart(chart_data, height=400)
                
                st.caption(f"最后刷新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 非交易时间可能无数据")
        
        except Exception as e:
            st.error(f"发生错误：{str(e)}")
            st.info("建议：\n1. 本地运行 pip install akshare --upgrade\n2. 检查是否交易日\n3. 查看上方列名调试信息")

st.markdown("---")
st.markdown("""
**免责声明**：估值数据来源于东方财富，仅供个人参考，不构成投资建议。以官方公布净值为准。  
**建议**：定期本地运行 `pip install --upgrade akshare streamlit pandas matplotlib` 保持更新。
""")
