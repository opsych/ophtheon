# 3score.py
import streamlit as st

# ---------------------------------------------------------
# 1. 스타일 (폰트 + 사이드바 숨김)
# ---------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Nanum+Gothic:wght@400;700&display=swap');

/* 전체 폰트 적용 */
html, body, [class*="css"] {
    font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
}

/* 메인 컨테이너 타이포 / 여백 */
.block-container {
    font-size: 16px !important;
    line-height: 1.65 !important;
    padding-top: 3rem;
    padding-bottom: 3rem;
}

/* 제목 크기 정리 */
h1 { font-size: 30px !important; font-weight: 600 !important; }
h2 { font-size: 26px !important; font-weight: 600 !important; }
h3 { font-size: 22px !important; font-weight: 500 !important; }
h4 { font-size: 18px !important; font-weight: 500 !important; }

/* 사이드바 완전 숨김 */
[data-testid="stSidebar"] {
    display: none !important;
}
/* 접기/펴기 버튼도 숨김 */
[data-testid="collapsedControl"] {
    display: none !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. 본문
# ---------------------------------------------------------
st.title("데이터 기반 자동 판정")

st.markdown(
    """
현재 동공 기반 자동 판정 로직은  
파일럿 연구 및 알고리즘 고도화 단계에 있습니다.

향후에는 검사 시 수집된 동공 시계열 데이터와  
질문 유형별 동공 크기를 기반으로,  

**실시간으로 진위 판정** 의견을 제시하는 형태로 제공될 예정입니다.
"""
)

st.info(
    "아직 연구중인 기능이지만 Ophtheon의 목표는,  "
    "AI 검사관이 진행하는 데이터 기반 자동 판정입니다."
)

st.write("")
st.markdown("---")

# ---------------------------------------------------------
# 3. 홈으로 이동 버튼
# ---------------------------------------------------------
if st.button("home"):
    st.switch_page("app.py")
