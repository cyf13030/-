# app.py - 个人基金估值小工具（2026 兼容版，已修复格式化错误）
import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="基金估值小工具", page_icon="📈", layout="wide")

st.title("个人基金估值查询")
st.caption(f"数据来源：东方财富估算净值 via AKShare | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

DEFAULT_FUNDS = [
    "110022",  # 易方达优选成长混合
    "001593",  # 南方成份精选混合
    "000001",  # 华夏成长混合
    "519697",  # 长信量化先锋股票
    # 在这里添加更多你的基金代码
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
            
            # 调试：显示实际返回的列名（部署后可见，便于排查）
            st.caption("调试信息：AKShare 返回的列名（用于排查接口变化）")
            st.code(", ".join(df.columns.tolist()), language="text")
            
            # 动态匹配列名（兼容旧/新版本）
            value_col = next((c for c in df.columns if any(k in c for k in ["估算值", "估值", "净值", "IOPV"])), None)
            growth_col = next((c for c in df.columns if any(k in c for k in ["增长率", "涨幅", "增长"])), None)
            bias_col = next((c for c in df.columns if any(k in c for k in ["偏差", "偏离"])), None)
            
            if not value_col or not growth_col:
                st.error("无法识别估算值或增长率列。请查看上方列名列表，告诉我具体列名，我帮你调整代码。")
                st.stop()
            
            # 提取关注的基金数据
            watched = df[df['基金代码'].isin(selected_funds)][['基金代码', '基金名称', value_col, growth_col]]
            if bias_col and bias_col in df.columns:
                watched[bias_col] = df[bias_col]
            
            # 重命名列为友好名称
            watched = watched.rename(columns={
                '基金代码': '代码',
                '基金名称': '名称',
                value_col: '估算净值',
                growth_col: '估算涨幅',
                bias_col: '偏差' if bias_col else None
            })
            
            # 关键清洗步骤：转数值，处理无效值
            # 估算净值列清洗
            watched['估算净值'] = (
                watched['估算净值'].astype(str)
                .str.replace(',', '', regex=False)
                .str.replace(' ', '', regex=False)
                .str.strip()
                .replace(['', '--', '暂无', '无数据'], float('nan'))
            )
            watched['估算净值'] = pd.to_numeric(watched['估算净值'], errors='coerce')
            
            # 估算涨幅列清洗（去 %，转 float）
            watched['估算涨幅(%)'] = (
                watched['估算涨幅'].astype(str)
                .str.replace('%', '', regex=False)
                .str.replace(' ', '', regex=False)
                .str.strip()
                .replace(['', '--', '暂无'], '0')
            )
            watched['估算涨幅(%)'] = pd.to_numeric(watched['估算涨幅(%)'], errors='coerce').fillna(0)
            
            # 偏差列（如果存在）
            if '偏差' in watched.columns:
                watched['偏差'] = (
                    watched['偏差'].astype(str)
                    .str.replace('%', '', regex=False)
                    .str.strip()
                    .replace(['', '--'], '0')
                )
                watched['偏差'] = pd.to_numeric(watched['偏差'], errors='coerce').fillna(0)
            
            # 排序
            watched = watched.sort_values('估算涨幅(%)', ascending=False).reset_index(drop=True)
            
            # 显示表格
            st.subheader(f"估值快照（找到 {len(watched)} 只基金）")
            
            def format_value(val):
                if pd.isna(val):
                    return "—"
                return f"{val:.4f}"
            
            def format_growth(val):
                if pd.isna(val):
                    return "—"
                return f"{val:+.2f}%"
            
            def format_bias(val):
                if pd.isna(val):
                    return "—"
                return f"{val:.2f}%"
            
            styled = watched.style.format({
                '估算净值': format_value,
                '估算涨幅(%)': format_growth,
                '偏差': format_bias if '偏差' in watched.columns else None
            }).background_gradient(
                subset=['估算涨幅(%)'],
                cmap='RdYlGn',
                vmin=-5,
                vmax=5
            )
            
            st.dataframe(styled, use_container_width=True)
            
            # 柱状图
            st.subheader("估算涨幅对比")
            chart_data = watched.set_index('名称')['估算涨幅(%)'].fillna(0)
            st.bar_chart(chart_data, height=400)
            
            st.caption(f"最后刷新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 非交易时间或代码错误可能无数据")
        
        except Exception as e:
            st.error(f"数据拉取或处理失败：{str(e)}")
            st.info("常见解决：\n1. pip install akshare --upgrade（本地测试用）\n2. 检查网络或是否交易日\n3. 查看上方列名调试信息")

st.markdown("---")
st.markdown("""
**免责声明**：估值数据来源于东方财富，仅供个人参考，不构成投资建议。以官方公布净值为准。  
**建议**：定期本地运行 `pip install --upgrade akshare streamlit pandas matplotlib` 保持更新。
""")

                st.bar_chart(watched.set_index('名称')['估算涨幅(%)'])

        except Exception as e:
            st.error(f"错误：{str(e)}")
            st.info("建议：升级 AKShare (pip install akshare --upgrade)，检查网络，或非交易时间数据为空。")

st.markdown("---")
st.caption("个人工具 | 数据仅参考 | AKShare + Streamlit")
