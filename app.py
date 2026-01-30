# app.py - 极简修复版（语法干净，功能完整）
import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="基金估值小工具", page_icon="📈", layout="wide")

st.title("个人基金估值查询")
st.caption(f"东方财富估算数据 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

DEFAULT_FUNDS = ["110022", "001593", "000001", "519697"]

with st.sidebar:
    st.header("选择基金")
    selected_funds = st.multiselect(
        "关注的基金",
        options=DEFAULT_FUNDS + ["其他"],
        default=DEFAULT_FUNDS[:3]
    )
    
    custom = st.text_input("手动输入代码（逗号分隔）", "")
    if custom:
        extras = [c.strip() for c in custom.split(",") if c.strip().isdigit() and len(c.strip()) == 6]
        selected_funds = list(set(selected_funds + extras))
    
    st.button("刷新数据", type="primary")  # 按钮点击会自动 rerun

if not selected_funds:
    st.info("请选择或输入至少一个基金代码")
else:
    with st.spinner("拉取数据中..."):
        try:
            df = ak.fund_value_estimation_em(symbol="全部")
            df['基金代码'] = df['基金代码'].astype(str).str.zfill(6)
            
            # 显示列名调试
            st.caption("当前列名（调试用）：")
            st.code(", ".join(df.columns.tolist()))
            
            # 动态找列
            value_col = next((c for c in df.columns if '估算值' in c), None)
            growth_col = next((c for c in df.columns if '估算增长率' in c or '增长率' in c), None)
            bias_col = next((c for c in df.columns if '偏差' in c), None)
            
            if not value_col or not growth_col:
                st.error("列名匹配失败，请把上方列名列表复制给我调整代码。")
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
                
                # 转数值 + 清洗
                watched['估算净值'] = pd.to_numeric(
                    watched['估算净值'].astype(str).str.replace(',', '').str.strip().replace(['', '--', '无'], float('nan')),
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
                
                watched = watched.sort_values('估算涨幅(%)', ascending=False).reset_index(drop=True)
                
                # 格式化显示
                def fmt_float(x): return "—" if pd.isna(x) else f"{x:.4f}"
                def fmt_pct(x):   return "—" if pd.isna(x) else f"{x:+.2f}%"
                
                st.subheader(f"估值快照（{len(watched)} 只）")
                st.dataframe(
                    watched.style.format({
                        '估算净值': fmt_float,
                        '估算涨幅(%)': fmt_pct,
                        '偏差': fmt_pct if '偏差' in watched.columns else None
                    }).background_gradient(subset=['估算涨幅(%)'], cmap='RdYlGn', vmin=-5, vmax=5),
                    use_container_width=True
                )
                
                st.subheader("涨幅对比")
                st.bar_chart(watched.set_index('名称')['估算涨幅(%)'].fillna(0), height=350)
                
                st.caption("数据仅参考 | 非交易时间可能为空")
        
        except Exception as e:
            st.error(f"错误：{str(e)}")

st.markdown("---")
st.caption("个人工具 | 数据来源东方财富 | 仅供参考")    
    if st.button("🔄 刷新数据", type="primary"):
        st.rerun()

if not selected_funds:
    st.info("请至少选择或输入一个基金代码")
else:
    with st.spinner("正在拉取东方财富估算数据..."):
        try:
            df = ak.fund_value_estimation_em(symbol="全部")
            df['基金代码'] = df['基金代码'].astype(str).str.zfill(6)
            
            st.caption("调试：AKShare 当前返回的列名")
            st.code(", ".join(df.columns.tolist()), language="text")
            
            value_col = next((c for c in df.columns if '估算值' in c), None)
            growth_col = next((c for c in df.columns if '估算增长率' in c), None)
            bias_col = next((c for c in df.columns if '偏差' in c), None)
            
            if not value_col or not growth_col:
                st.error("无法识别估算值或增长率列。请复制上方列名列表给我，我继续调整。")
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
                
                # 清洗数据
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
                
                watched = watched.sort_values('估算涨幅(%)', ascending=False).reset_index(drop=True)
                
                def safe_float(val, dec=4):
                    return "—" if pd.isna(val) else f"{val:.{dec}f}"
                
                def safe_pct(val):
                    return "—" if pd.isna(val) else f"{val:+.2f}%"
                
                st.subheader(f"估值快照（{len(watched)} 只）")
                st.dataframe(
                    watched.style.format({
                        '估算净值': lambda x: safe_float(x, 4),
                        '估算涨幅(%)': safe_pct,
                        '偏差': safe_pct if '偏差' in watched else None
                    }).background_gradient(subset=['估算涨幅(%)'], cmap='RdYlGn', vmin=-5, vmax=5),
                    use_container_width=True
                )
                
                st.subheader("估算涨幅对比")
                st.bar_chart(watched.set_index('名称')['估算涨幅(%)'].fillna(0), height=400)
                
                st.caption(f"最后刷新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 非交易日可能无数据")
        
        except Exception as e:
            st.error(f"错误：{str(e)}")
            st.info("建议：升级 AKShare 或检查网络")

st.markdown("---")
st.markdown("""
**免责声明**：估值数据来源于东方财富，仅供个人参考，不构成投资建议。以官方公布净值为准。  
**建议**：定期本地运行 `pip install --upgrade akshare streamlit pandas matplotlib` 保持更新。
""")        selected_funds = list(set(selected_funds + extras))
    
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
            st.caption("调试：AKShare 当前返回的列名")
            st.code(", ".join(df.columns.tolist()), language="text")
            
            # 动态匹配（使用 'in' 包含匹配，兼容带日期的前缀）
            value_col = next((c for c in df.columns if '估算值' in c), None)
            growth_col = next((c for c in df.columns if '估算增长率' in c), None)
            bias_col = next((c for c in df.columns if '偏差' in c), None)
            
            if not value_col or not growth_col:
                st.error("仍无法识别估算值或增长率列。请把上方列名列表完整复制给我，我继续优化匹配逻辑。")
            else:
                cols = ['基金代码', '基金名称', value_col, growth_col]
                if bias_col:
                    cols.append(bias_col)
                
                watched = df[df['基金代码'].isin(selected_funds)][cols].copy()
                
                # 重命名（使用动态列名）
                watched = watched.rename(columns={
                    '基金代码': '代码',
                    '基金名称': '名称',
                    value_col: '估算净值',
                    growth_col: '估算涨幅',
                })
                if bias_col:
                    watched = watched.rename(columns={bias_col: '偏差'})
                
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
                
                # 表格
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
            st.info("建议：\n1. 本地 pip install akshare --upgrade\n2. 检查网络或交易日\n3. 查看上方列名")

st.markdown("---")
st.markdown("""
**免责声明**：估值数据来源于东方财富，仅供个人参考，不构成投资建议。以官方公布净值为准。  
**建议**：定期本地运行 `pip install --upgrade akshare streamlit pandas matplotlib` 保持更新。
""")    if st.button("🔄 刷新数据", type="primary"):
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
