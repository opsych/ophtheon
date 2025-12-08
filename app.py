# app.py
import streamlit as st

st.set_page_config(
    page_title="Ophtheon — prototype v0",
    page_icon="🕵🏻‍♂️",
    layout="centered",
)

st.title("Ophtheon — prototype v0")
st.subheader("동공 기반 거짓말 탐지 시스템: 옵시언")

st.markdown(
    """
Ophtheon은 **동공(pupil)** 반응을 기반으로
진술의 진위를 스크리닝하는 자동 판정 거짓말 탐지 시스템입니다.
"""
)

st.write("")  # 약간 여백

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link(
        "pages/1pretest.py",
        label="검사 전 안내 및 연습",
        icon="📝",
        use_container_width=True,
    )

with col2:
    st.page_link(
        "pages/2test.py",
        label="검사 시행",
        icon="🕵🏻‍♂️",
        use_container_width=True,
    )

with col3:
    st.page_link(
        "pages/3score.py",
        label="데이터 기반 자동 판정",
        icon="📊",
        use_container_width=True,
    )

st.write("")
st.caption("© 2025 QnFP Lab · Jung Joo Lee")
