# app.py
import streamlit as st
import pandas as pd

st.markdown("""
<style>
.main > div {
    padding-top: 180px !important;
    }
/* 1) Google Fonts에서 Sora + Nanum Gothic 로드 */
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Nanum+Gothic:wght@400;700&display=swap');

/* 2) 전체 기본 폰트: 영문은 Sora, 한글은 Nanum Gothic으로 자동 fallback */
html, body, [class*="css"]  {
    font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
}

/* 3) 제목(H1~H6)도 동일 폰트 사용 (조금 더 두껍게) */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
    font-weight: 600 !important;
}

/* 4) 기본 위젯(버튼, 인풋 등)에 폰트 강제 적용 */
.stButton button,
.stTextInput input,
.stSelectbox div,
.stRadio label,
.stCheckbox label,
.stTextArea textarea {
    font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="Ophtheon — prototype v0",
    page_icon="🕵🏻‍♂️️",
    layout="centered",
)

# ---------- 상태 초기화 ----------
if "step" not in st.session_state:
    st.session_state["step"] = "home"

if "info" not in st.session_state:
    st.session_state["info"] = {}

if "data" not in st.session_state:
    st.session_state["data"] = None

if "score" not in st.session_state:
    st.session_state["score"] = None

step = st.session_state["step"]

# ---------- 공통 함수 ----------

def goto(next_step: str):
    st.session_state["step"] = next_step
    st.experimental_rerun()


# ---------- 1) 홈 ----------
if step == "home":
    st.title("Ophtheon — prototype v0")
    st.subheader("동공 기반 거짓말 탐지 시스템")

    st.markdown("""
Ophtheon은 **동공(pupil)** 반응을 이용해  
진술의 진위를 스크리닝하는 비접촉·자동 채점 거짓말 탐지 시스템입니다.
""")

    if st.button("시작하기"):
        goto("info")

    st.caption("© 2025 QnFP Lab · Jung Joo Lee")
    

# ---------- 2) 정보 입력 ----------
elif step == "info":
    st.title("1. 정보 입력")

    st.markdown("검사에 앞서 기본 정보를 입력해주세요.")

    name = st.text_input("이름")
    gender = st.radio("성별", ["남", "여", "기타"], horizontal=True)
    age = st.number_input("나이", min_value=18, max_value=70, value=25, step=1)

    st.markdown("---")
    st.markdown("### 최근 24시간 내 상태")

    sleep_hours = st.slider("지난 24시간 동안 수면 시간(시간)", 0, 12, 7)

    med_use = st.radio("복용 중인 약물이 있습니까?", ["무", "유"], horizontal=True)
    med_detail = ""
    if med_use == "유":
        med_detail = st.text_input("복용 중인 약물 종류를 적어주세요.", placeholder="예: 항우울제, 수면제 등")

    alcohol = st.radio("지난 24시간 내 음주 여부", ["무", "유"], horizontal=True)
    smoking = st.radio("지난 24시간 내 흡연 여부", ["무", "유"], horizontal=True)
    caffeine = st.radio("지난 12시간 내 카페인 섭취 여부", ["무", "유"], horizontal=True)

    st.markdown("---")
    st.markdown("### 사건 관련 핵심 주장")

    claim = st.text_area(
        f"사건에서 밝히고자 하는 **{name or '피검자'}** 님의 핵심 주장을 적어주세요.",
        placeholder="예) 저는 000을 때린 적이 없습니다."
    )

    agree = st.radio("검사 진행에 동의하십니까?", ["동의함", "동의하지 않음"], horizontal=True)

    st.markdown("---")

    # R 질문 자동 초안 생성 (아주 단순 v0)
    r_question_auto = ""
    if name and claim:
        r_question_auto = f"{name}님, \"{claim}\"라는 진술은 사실입니까?"

    if r_question_auto:
        st.markdown("#### 자동 생성된 R 질문(초안)")
        st.info(r_question_auto)
        r_question_final = st.text_input("최종 R 질문 문장을 확인·수정해주세요.", value=r_question_auto)
    else:
        r_question_final = st.text_input("최종 R 질문 문장", placeholder="핵심 관련 질문을 작성해주세요.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅︎ 처음으로"):
            goto("home")

    with col2:
        if st.button("사전 면담 단계로 ➜"):
            if agree != "동의함":
                st.error("검사에 동의하지 않으면 검사를 진행할 수 없습니다.")
            elif not name or not claim:
                st.error("이름과 핵심 주장은 반드시 입력해주세요.")
            else:
                st.session_state["info"] = {
                    "name": name,
                    "gender": gender,
                    "age": age,
                    "sleep_hours": sleep_hours,
                    "med_use": med_use,
                    "med_detail": med_detail,
                    "alcohol": alcohol,
                    "smoking": smoking,
                    "caffeine": caffeine,
                    "claim": claim,
                    "agree": agree,
                    "r_question": r_question_final,
                }
                goto("interview")


# ---------- 3) 사전 면담 ----------
elif step == "interview":
    info = st.session_state["info"]
    name = info.get("name", "(이름 미지정)")

    st.title("2. 사전 면담 (자동 안내)")

    st.markdown(f"""
피검자 **{name}** 님, 안녕하세요.  
지금부터 Ophtheon 시스템이 검사의 목적과 절차를 간단히 설명드리겠습니다.

- 이 검사는 형사 절차에서 강제력이 있는 조사는 아니며,  
  동공 반응을 이용해 **긴장도와 반응 패턴**을 확인하는 *스크리닝* 용도입니다.
- 검사는 총 **비교 질문(C)**, **관련 질문(R)**, **중립 질문(N)** 으로 구성됩니다.
""")

    st.markdown("#### 검사 원리 설명")
    st.info("""
사람은 거짓말을 하거나 중요하다고 느끼는 질문을 들을 때  
무의식적으로 동공이 조금 더 커집니다.  

Ophtheon은 질문 유형별 동공 반응을 비교해  
비교 질문(C)에 비해 관련 질문(R)에서 반응이 더 큰지 확인하고,  
그 차이(ΔC–ΔR)를 자동으로 계산합니다.
""")

    st.markdown("#### 이번 검사에서 사용할 R 질문(초안)")
    st.write(f"👉 **{info.get('r_question', '(R 질문 미입력)')}**")

    st.markdown("""
잠시 후 본 검사 단계에서는  
위 질문을 포함한 여러 질문을 들으시게 되며,  
각 질문마다 '예' 또는 '아니오'로만 답변하시면 됩니다.
""")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅︎ 정보 수정"):
            goto("info")
    with col2:
        if st.button("검사 단계로 ➜"):
            goto("exam")


# ---------- 4) 검사 / 데이터 업로드 (v0) ----------
elif step == "exam":
    st.title("3. 본 검사 (v0: 데이터 업로드 모드)")

    st.markdown("""
현재 v0 버전에서는 실제 검사 대신,  
이미 수집된 동공 데이터(CSV)를 업로드하여  
Ophtheon 채점 로직을 테스트합니다.
""")

    uploaded = st.file_uploader("동공 데이터 CSV 파일 업로드", type=["csv"])

    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.session_state["data"] = df
        st.write("데이터 미리보기:")
        st.dataframe(df.head())

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅︎ 사전 면담으로"):
            goto("interview")
    with col2:
        if st.button("채점 및 리포트 생성 ➜"):
            if st.session_state["data"] is None:
                st.error("먼저 CSV 데이터를 업로드해주세요.")
            else:
                # TODO: 실제 ΔC–ΔR 채점 로직으로 대체
                df = st.session_state["data"]
                # 여기서는 예시로 가짜 점수 생성
                st.session_state["score"] = {
                    "delta_example": 0.123,
                    "interpretation": "예시: 관련 질문에서 비교 질문보다 반응이 다소 크게 나타났습니다."
                }
                goto("report")


# ---------- 5) 리포트 ----------
elif step == "report":
    info = st.session_state["info"]
    score = st.session_state["score"]

    st.title("4. 자동 리포트 (v0)")
    st.markdown("검사가 완료되었습니다. 아래는 연구용 예시 리포트입니다.")

    st.markdown("### 기본 정보")
    st.write(f"- 피검자 이름/ID: **{info.get('name', '(미입력)')}**")
    st.write(f"- 성별 / 나이: {info.get('gender', '(미입력)')} / {info.get('age', '(미입력)')}세")
    st.write(f"- 핵심 주장: {info.get('claim', '(미입력)')}")

    st.markdown("---")
    st.markdown("### ΔC–ΔR 기반 예시 결과")
    st.write(score or "채점 결과가 없습니다. (v0 예시)")

    st.info("""
※ 본 결과는 Ophtheon v0 연구 프로토타입에서 산출된 값으로,  
   실제 수사·법적 판단에 단독으로 사용될 수 없습니다.
""")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅︎ 검사 다시 보기"):
            goto("exam")
    with col2:
        if st.button("처음으로 돌아가기 ⟳"):
            st.session_state.clear()
            goto("home")
