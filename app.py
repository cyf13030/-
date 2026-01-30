# app.py  (updated for 2026 AKShare compatibility)
import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="基金估值小工具", page_icon="📈", layout="wide")

st.title("个人基金估值查询")
st.caption(f"东方财富估算数据 via AKShare | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

DEFAULT_FUNDS = ["110022", "001593", "000001", "519697"]

with st.sidebar:
    st.header("选择基金")
    selected = st.multiselect("关注的基金", DEFAULT_FUNDS + ["其他"], default=DEFAULT_FUNDS[:3])
    custom = st.text_input("手动输入代码 (逗号分隔)", "")
    if custom:
        extras = [c.strip() for c in custom.split(",") if c.strip().isdigit() and len(c.strip()) == 6]
        selected = list(set(selected + extras))
    if st.button("刷新"):
        st.rerun()

if not selected:
    st.info("请选择或输入基金代码")
else:
    with st.spinner("获取数据..."):
        try:
            df = ak.fund_value_estimation_em(symbol="全部")
            df['基金代码'] = df['基金代码'].astype(str).str.zfill(6)

            # Debug: show actual columns
            st.caption("调试：当前接口返回的列名")
            st.code(", ".join(df.columns.tolist()), language="text")

            # Dynamic column mapping (add more aliases as seen in your logs)
            value_col = next((c for c in df.columns if "估算值" in c or "估值" in c or "IOPV" in c), None)
            growth_col = next((c for c in df.columns if "增长率" in c or "涨幅" in c or "增长" in c), None)
            bias_col = next((c for c in df.columns if "偏差" in c or "偏离" in c), None)

            if not value_col or not growth_col:
                st.error("无法识别估算值/增长率列。请查看上方列名列表，并告诉我，我帮你调整。")
            else:
                watched = df[df['基金代码'].isin(selected)][['基金代码', '基金名称', value_col, growth_col]]
                if bias_col:
                    watched[bias_col] = df[bias_col]

                watched = watched.rename(columns={
                    '基金代码': '代码',
                    '基金名称': '名称',
                    value_col: '估算净值',
                    growth_col: '估算涨幅',
                    bias_col: '偏差' if bias_col else None
                }).dropna(subset=['估算净值'], how='all')

                watched['估算涨幅(%)'] = watched['估算涨幅'].astype(str).str.replace('%', '').str.strip().replace('', '0').astype(float)

                watched = watched.sort_values('估算涨幅(%)', ascending=False)

                st.dataframe(
                    watched.style.format({
                        '估算净值': '{:.4f}',
                        '估算涨幅(%)': '{:+.2f}%',
                        '偏差': '{:.2f}%' if '偏差' in watched else None
                    }).background_gradient(subset=['估算涨幅(%)'], cmap='RdYlGn', vmin=-5, vmax=5),
                    use_container_width=True
                )

                st.bar_chart(watched.set_index('名称')['估算涨幅(%)'])

        except Exception as e:
            st.error(f"错误：{str(e)}")
            st.info("建议：升级 AKShare (pip install akshare --upgrade)，检查网络，或非交易时间数据为空。")

st.markdown("---")
st.caption("个人工具 | 数据仅参考 | AKShare + Streamlit")
