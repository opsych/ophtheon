# ophtheon/app.py
import streamlit as st

# ----------------------------------------
# Page Config
# ----------------------------------------
st.set_page_config(
    page_title="Ophtheon — prototype v0",
    page_icon="👁️",  # favicon 수준은 문제 없음
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------
# Custom CSS (Sora + Nanum Gothic 적용 + Sidebar 제거 + 미니멀 스타일)
# ----------------------------------------
custom_css = """
<style>
/* Load custom fonts */
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400&display=swap');

/* Apply fonts globally */
html, body, [class*="css"] {
    font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
}

/* Hide Streamlit sidebar */
[data-testid="stSidebar"] {
    display: none !important;
}

/* Adjust main padding */
.block-container {
    padding-top: 4rem;
    padding-bottom: 4rem;
}

/* Minimal header styling */
h1, h2, h3 {
    font-weight: 600 !important;
}

/* Buttons: minimal, modern */
.st-emotion-cache-17eq0hr {
    border-radius: 10px !important;
    border: 1px solid #ddd !important;
    padding: 14px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

/* Slight hover effect */
.st-emotion-cache-17eq0hr:hover {
    border-color: #333 !important;
}

/* Caption minimal tone */
footer, .caption, .stCaption {
    color: #888 !important;
    font-size: 12px !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ----------------------------------------
# Layout
# ----------------------------------------
st.title("Ophtheon — prototype v0")
st.subheader("동공 기반 거짓말 탐지 시스템")

st.markdown(
    """
Ophtheon은 **동공(pupil) 반응**을 측정하여  
주장의 진위를 스크리닝하는 AI 기반 거짓말 탐지 시스템입니다.
"""
)

st.write("")  # spacing

# ----------------------------------------
# Navigation Button Row (Minimal)
# ----------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.page_link(
        "pages/1pretest.py",
        label="검사 전 안내 및 연습",
        use_container_width=True,
    )

with col2:
    st.page_link(
        "pages/2test.py",
        label="검사 시행",
        use_container_width=True,
    )

with col3:
    st.page_link(
        "pages/3score.py",
        label="자동 판정 결과",
        use_container_width=True,
    )

st.write("")
st.caption("© 2025 Ophtheon · J. Lee & Y. Cho")
