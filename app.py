# app.py
import streamlit as st
import pandas as pd
import random
import io
import streamlit.components.v1 as components

# ---------------------------------------------------------
# 0. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="Ophtheon — prototype v0",
    page_icon="🕵🏻‍♂️",
    layout="centered",
)

# ---------------------------------------------------------
# 1. 공통 스타일 (폰트)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    /* -----------------------------
       FONT FAMILY
    ------------------------------*/
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Nanum+Gothic:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
        font-weight: 600 !important;
        margin-top: 0.5em !important;
        margin-bottom: 0.5em !important;
    }

    /* -----------------------------
       GLOBAL TEXT SIZE (본문)
    ------------------------------*/
    html, body, p, div, span, label {
        font-size: 18px !important;
        line-height: 1.6 !important;
    }

    /* -----------------------------
       TITLES
    ------------------------------*/
    h1 { font-size: 32px !important; }
    h2 { font-size: 28px !important; }
    h3 { font-size: 24px !important; }
    h4 { font-size: 20px !important; }

    /* -----------------------------
       RADIO / CHECKBOX LABEL SIZE
    ------------------------------*/
    .stRadio > label, .stRadio div {
        font-size: 18px !important;
    }

    .stCheckbox label {
        font-size: 18px !important;
    }

    /* -----------------------------
       TEXT INPUT / SELECT BOX
    ------------------------------*/
    .stTextInput input,
    .stSelectbox div,
    .stTextArea textarea {
        font-size: 18px !important;
    }

    /* -----------------------------
       SLIDER LABEL / VALUE
    ------------------------------*/
    .stSlider label,
    .stSlider span {
        font-size: 18px !important;
    }

    /* -----------------------------
       ALERT BOX (success/info/warn)
    ------------------------------*/
    .stAlert > div {
        font-size: 18px !important;
        line-height: 1.5 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. 상태 초기화
# ---------------------------------------------------------
if "mode" not in st.session_state:
    st.session_state["mode"] = "none"   # 'interview' / 'upload'

if "step" not in st.session_state:
    st.session_state["step"] = "home"

if "case_info" not in st.session_state:
    st.session_state["case_info"] = {}

if "dlcq_answers" not in st.session_state:
    st.session_state["dlcq_answers"] = {}

if "cq_indices" not in st.session_state:
    st.session_state["cq_indices"] = []

if "question_set" not in st.session_state:
    st.session_state["question_set"] = None

if "data" not in st.session_state:
    st.session_state["data"] = None

step = st.session_state["step"]
mode = st.session_state["mode"]


# ---------------------------------------------------------
# 공용 함수
# ---------------------------------------------------------
def goto(next_step: str):
    st.session_state["step"] = next_step
    st.rerun()


def reset_all():
    for key in [
        "mode",
        "step",
        "case_info",
        "dlcq_answers",
        "cq_indices",
        "question_set",
        "data",
    ]:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state["mode"] = "none"
    st.session_state["step"] = "home"

    st.rerun()
# ---------------------------------------------------------
# 질문 템플릿 함수들
# ---------------------------------------------------------
def make_core_claim_suspect(offense_text: str) -> str:
    return f"저는 {offense_text}한 사실이 없습니다."


def make_core_claim_victim(offense_text: str) -> str:
    return f"저는 {offense_text}을/를 당했습니다."


def make_r_questions_suspect(offense_text: str) -> list[str]:
    return [
        f"당신은 그 당시 {offense_text}을/를 한 사실이 있습니까?",
        f"당신은 직접 {offense_text}한 적이 있습니까?",
        f"당신이 {offense_text}을/를 한 것이 사실입니까?",
    ]


def make_r_questions_victim(offense_text: str) -> list[str]:
    return [
        f"당신은 그 당시 피의자로부터 {offense_text}을/를 당한 사실이 있습니까?",
        f"당신은 피의자에게 직접 {offense_text}을/를 당한 적이 있습니까?",
        f"당신은 피의자로부터 {offense_text} 피해를 입은 것이 사실입니까?",
    ]


# I / SR 질문 텍스트 (고정)
I_QUESTION = "당신은 오늘 검사관이 연습한 것만 질문한다는 것을 믿습니까?"
SR_QUESTION = "당신은 오늘 검사관이 묻는 질문에 사실대로 대답하겠습니까?"


# 성향 설문 문항 (DLCQ 후보)
DLCQ_ITEMS = [
    "당신은 지금까지 살면서 가족이나 친구에게 거짓말을 해본 적이 있습니까?",
    "당신은 지금까지 살면서 누군가에게 단 한 번이라도 거짓말을 한 적이 있습니까?",
    "당신은 지금까지 살면서 실수를 저지른 뒤 그것을 비밀로 한 적이 있습니까?",
    "당신은 지금까지 살면서 규칙이나 규정을 어긴 적이 있습니까?",
    "당신은 지금까지 살면서 책임을 피하기 위해 거짓말을 한 적이 있습니까?",
    "당신은 지금까지 살면서 다른 사람의 흉이나 뒷담화를 한 적이 있습니까?",
    "당신은 지금까지 살면서 본인의 잘못을 타인에게 돌린 적이 있습니까?",
    "당신은 지금까지 살면서 가족들에게 말하지 못한 비밀이 있습니까?",
    "당신은 지금까지 살면서 본인의 잘못을 숨긴 사실이 있습니까?",
    "당신은 지금까지 살면서 없는 말을 꾸며서 말한 적이 있습니까?",
    "당신은 지금까지 살면서 나쁜 행동을 해본 적이 있습니까?",
    "당신은 지금까지 살면서 주변 사람들이 알면 안 되는 행동을 한 사실이 있습니까?",
    "당신은 지금까지 살면서 잘못된 것임을 알고도 행동한 적이 있습니까?",
    "당신은 지금까지 살면서 본인을 위해 남에게 피해를 준 적이 있습니까?",
    "당신은 지금까지 살면서 다른 사람을 미워하거나 시기한 적이 있습니까?",
    "당신은 지금까지 살면서 양심에 찔리는 행동을 한 적이 있습니까?",
    "당신은 지금까지 살면서 다른 사람에게 상처 되는 말을 한 적이 있습니까?",
]


def pick_cq_indices(dlcq_answers: dict[int, bool], k: int = 3) -> list[int]:
    """DLCQ에서 '예'라고 응답한 문항 중 k개 선택."""
    yes_indices = [i for i, ans in dlcq_answers.items() if ans]
    if len(yes_indices) == 0:
        return []
    if len(yes_indices) <= k:
        return yes_indices
    return random.sample(yes_indices, k)


# ---------------------------------------------------------
# 홈 화면: 모드 선택
# ---------------------------------------------------------
if step == "home":
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 140px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Ophtheon — prototype v0")
    st.subheader("동공 기반 거짓말 탐지 시스템")

    st.markdown(
        """
        Ophtheon은 **동공(pupil)** 반응을 이용해  
        진술의 진위를 스크리닝하는 비접촉·자동 채점 거짓말 탐지 시스템입니다.
        """
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("검사 전 안내 및 연습", use_container_width=True):
            st.session_state["mode"] = "interview"
            st.session_state["step"] = "interview_info"
            st.rerun()
    with col2:
        if st.button("데이터 업로드 및 자동 판정", use_container_width=True):
            st.session_state["mode"] = "upload"
            st.session_state["step"] = "upload"
            st.rerun()

    st.write("")
    st.caption("© 2025 QnFP Lab · Jung Joo Lee")


# ---------------------------------------------------------
# 모드: 사전 면담 & 질문 생성
# ---------------------------------------------------------
elif mode == "interview":

    # ---------- 1) 정보 입력 ----------
    if step == "interview_info":
        st.title("기본 정보 입력")

        role = st.radio(
            "이번 사건에서 본인의 위치를 선택해 주세요.",
            ["피의자", "피해자"],
            horizontal=True,
        )
        role_key = "suspect" if role == "피의자" else "victim"

        offense_category = st.selectbox(
            "사건의 대분류를 선택해 주세요.",
            [
                "과제",
                "성범죄",
                "폭력범죄",
                "재산범죄",
                "공무원범죄",
                "사이버범죄",
                "교통범죄",
                "성매매",
                "마약",
                "기타",
            ],
        )

        if offense_category == "성범죄":
            offense_type = st.selectbox(
                "사건의 세부유형을 선택해 주세요.",
                ["성희롱", "강제추행", "강간", "불법촬영", "기타"],
            )
        elif offense_category == "폭력범죄":
            offense_type = st.selectbox(
                "사건의 세부유형을 선택해 주세요.",
                ["폭행", "상해", "협박", "체포·감금", "기타"],
            )
        elif offense_category == "과제":
            offense_type = st.selectbox(
                "사건의 세부유형을 선택해 주세요.",
                ["빨간 버튼 클릭"],
            )
        else:
            offense_type = st.selectbox(
                "사건의 세부유형을 선택해 주세요.",
                ["기타"],
            )

        offense_free = ""
        if offense_type == "기타":
            offense_free = st.text_input(
                "어떤 행위에 관한 사건인지 간단히 적어주세요.",
                placeholder="예) 금품 갈취, 사기 판매, 주거 침입, ...",
            )

        if offense_type == "기타":
            offense_text = offense_free.strip() if offense_free else "행위를"
        else:
            offense_text = offense_type

        st.markdown("---")
        st.markdown("### 기본 인적 사항")

        name = st.text_input("이름 또는 피검자 ID")
        gender = st.radio("성별", ["남성", "여성", "기타"], horizontal=True)
        age = st.number_input("나이", min_value=18, max_value=80, value=25, step=1)

        st.markdown("### 최근 상태")

        sleep_hours = st.slider("지난 24시간 동안 수면 시간(시간)", 0, 12, 7)

        med_use = st.radio("복용 중인 약물이 있습니까?", ["무", "유"], horizontal=True)
        med_detail = ""
        if med_use == "유":
            med_detail = st.text_input(
                "복용 중인 약물 종류를 적어주세요.",
                placeholder="예: 항우울제, 수면제 등"
            )

        alcohol = st.radio("지난 24시간 내 음주 여부", ["무", "유"], horizontal=True)
        smoking = st.radio("지난 24시간 내 흡연 여부", ["무", "유"], horizontal=True)
        caffeine = st.radio("지난 12시간 내 카페인 섭취 여부", ["무", "유"], horizontal=True)

        # 저장
        st.session_state["case_info"].update({
            "sleep_hours": sleep_hours,
            "med_use": med_use,
            "med_detail": med_detail,
            "alcohol": alcohol,
            "smoking": smoking,
            "caffeine": caffeine,
        })
        
        st.markdown("### 검사 동의")

        agree = st.radio("검사 진행에 동의하십니까?", ["동의함", "동의하지 않음"], horizontal=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                reset_all()
        with col2:
            if st.button("→"):
                if agree != "동의함":
                    st.error("검사에 동의하지 않으면 검사를 진행할 수 없습니다.")
                elif not name or not offense_text:
                    st.error("이름과 사건 정보는 반드시 입력해 주세요.")
                else:
                    if role_key == "suspect":
                        core_claim = make_core_claim_suspect(offense_text)
                    else:
                        core_claim = make_core_claim_victim(offense_text)

                    st.session_state["case_info"] = {
                        "role": role_key,
                        "role_label": role,
                        "offense_category": offense_category,
                        "offense_type": offense_type,
                        "offense_text": offense_text,
                        "core_claim": core_claim,
                        "name": name,
                        "gender": gender,
                        "age": age,
                    }
                    goto("interview_principle")

    # ---------- 2) 검사 소개 + 원리 ----------
    elif step == "interview_principle":
        info = st.session_state["case_info"]
        name = info.get("name", "(이름 미지정)")

        st.markdown(
            f"""
            피검자 **{name}** 님, 안녕하세요.  

            오늘 진행되는 Ophtheon 검사는 총 **11가지 질문**으로 구성됩니다.  
            모든 질문은 검사 전에 미리 알려드리고,  
            실제 검사에 앞서 충분히 연습할 수 있도록 설계되어 있습니다.
            """
        )

        st.info(
            """
            Ophtheon 검사는 **동공(pupil)** 반응을 이용해  
            질문 유형별 정서적 각성 패턴을 살펴보는 *스크리닝 검사*입니다.

            사람이 거짓말을 할 때에는 죄책감, 불안, 긴장감 등이 생기고,  
            이러한 감정은 자율신경계의 생리적 변화를 일으킵니다.

            특히, 심리적으로 중요한 질문을 듣거나 거짓을 말할 때  
            동공이 무의식적으로 조금 더 커지며, 이는 의도적으로 통제하기 어렵습니다.
            """
        )

        st.markdown(
            """
            다음을 눌러 계속 진행해주세요.
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_info")
        with col2:
            if st.button("→"):
                goto("interview_isr_intro")

    # ---------- 3) I/SR 안내 ----------
    elif step == "interview_isr_intro":
        st.title("기초 질문 안내")

        st.markdown(
            """
            검사의 도입 부분에는, 검사를 어떻게 진행할 것인지에 대한  
            간단한 **기초 질문 두 가지**가 포함되어 있습니다.
            """
        )


        st.markdown(
            """
            다음 화면에서 실제 검사와 같은 방식으로
            **'예' 혹은 '아니오'** 로 답변해보는  
            연습을 진행하겠습니다.
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_principle")
        with col2:
            if st.button("→"):
                goto("interview_isr_practice")

    # ---------- 4) I/SR 연습 (라디오 위에 설명 없음) ----------
    elif step == "interview_isr_practice":
        st.title("기초 질문 연습")

        all_correct = True

        ans_i = st.radio(
            I_QUESTION,
            ["선택 안 함", "예", "아니오"],
            index=0,
            key="isr_I",
        )
        if ans_i != "예":
            all_correct = False

        ans_sr = st.radio(
            SR_QUESTION,
            ["선택 안 함", "예", "아니오"],
            index=0,
            key="isr_SR",
        )
        if ans_sr != "예":
            all_correct = False

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_isr_intro")
        with col2:
            if st.button("→"):
                if ans_i == "선택 안 함" or ans_sr == "선택 안 함":
                    st.error("두 문항 모두에 대해 '예' 또는 '아니오'를 선택해 주세요.")
                elif not all_correct:
                    st.error("기초 질문 두 문항은 모두 '예'라고 응답해야 검사를 진행할 수 있습니다.")
                else:
                    goto("interview_r_intro")

    # ---------- 5) R 안내 ----------
    elif step == "interview_r_intro":
        info = st.session_state["case_info"]
        offense_text = info["offense_text"]
        core_claim = info["core_claim"]

        st.title("사건 관련 질문 안내")

        st.markdown("#### 피검자의 핵심 주장")
        st.info(core_claim)

        st.markdown(
            """
            이제 이번 사건과 직접 관련된 **사건 관련 질문** 을 안내해 드리겠습니다.  

            사건 관련 질문은 피검자님의 주장과 관련된 세 문항으로 구성되며,  
            실제 검사에서는 각 문항에 대해 **'예' 혹은 '아니오'** 로 응답하게 됩니다.

            다음 화면에서 세 문항을 제시하고, 실제 검사와 같은 방식으로  
            예/아니오 응답을 연습해 보겠습니다.
            """
        )

        role_key = info["role"]
        if role_key == "suspect":
            r_questions = make_r_questions_suspect(offense_text)
        else:
            r_questions = make_r_questions_victim(offense_text)

        st.session_state["case_info"]["R_questions"] = r_questions

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_isr_practice")
        with col2:
            if st.button("→"):
                goto("interview_r_practice")

    # ---------- 6) R 연습 ----------
    elif step == "interview_r_practice":
        info = st.session_state["case_info"]
        role_key = info["role"]
        r_questions = info.get("R_questions", [])

        st.title("사건 관련 질문 연습")

        if not r_questions:
            st.error("사건 관련 질문이 생성되지 않았습니다. 이전 단계로 돌아가 주세요.")
            if st.button("←"):
                goto("interview_r_intro")
        else:
            all_answered = True
            r_conflict = False  # 핵심 주장과 어긋나는 응답

            for i, q in enumerate(r_questions, start=1):
                ans = st.radio(
                    f"{q}",
                    ["선택 안 함", "예", "아니오"],
                    index=0,
                    key=f"r_practice_{i}",
                )
                if ans == "선택 안 함":
                    all_answered = False
                else:
                    # 기대 응답: 피의자 → '아니오', 피해자 → '예'
                    expected = "아니오" if role_key == "suspect" else "예"
                    if ans != expected:
                        r_conflict = True

            col1, col2 = st.columns(2)
            with col1:
                if st.button("←"):
                    goto("interview_r_intro")
            with col2:
                if st.button("→"):
                    if not all_answered:
                        st.error("세 문항 모두에 대해 '예' 또는 '아니오'를 선택해 주세요.")
                    elif r_conflict:
                        if role_key == "suspect":
                            st.error(
                                "사건 관련 질문에 '예'라고 응답하면 가해 사실을 인정하는 것으로 해석됩니다. "
                                "이 경우 거짓말탐지 검사의 대상이 될 수 없으므로, 검사관과 상의해 주세요."
                            )
                        else:
                            st.error(
                                "사건 관련 질문에 '아니오'로 응답하면 앞서 입력한 피해 주장과 어긋납니다. "
                                "검사관과 상의해 주세요."
                            )
                    else:
                        goto("interview_dlcq_intro")

    # ---------- 7) DLCQ 안내 ----------
    elif step == "interview_dlcq_intro":
        st.title("성향 설문 안내")

        st.markdown(
            """
            다음으로, 지금까지의 삶에서 있었던 행동 경험에 대해 묻는  
            **성향 설문** 을 진행합니다.

            이 설문에서 **'예'라고 응답한 문항들** 중 일부가 이후에  
            **성향 질문** 으로 사용됩니다.

            다음 화면에서 각 문항에 대해 솔직하게 예/아니오를 선택해 주세요.
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_r_practice")
        with col2:
            if st.button("→"):
                goto("interview_dlcq")

    # ---------- 8) DLCQ 설문 ----------
    elif step == "interview_dlcq":
        st.title("성향 설문 응답")

        answers = {}
        for idx, item in enumerate(DLCQ_ITEMS):
            ans = st.radio(
                item,
                ["응답 안 함", "예", "아니오"],
                index=0,
                key=f"dlcq_{idx}",
            )
            if ans == "예":
                answers[idx] = True
            elif ans == "아니오":
                answers[idx] = False

        st.session_state["dlcq_answers"] = answers

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_dlcq_intro")
        with col2:
            if st.button("→"):
                if not any(answers.values()):
                    st.error("적어도 세 문항 이상 '예'로 응답해야 성향 질문을 만들 수 있습니다.")
                else:
                    cq_indices = pick_cq_indices(answers, k=3)
                    st.session_state["cq_indices"] = cq_indices
                    goto("interview_c_intro")

    # ---------- 9) C 안내 ----------
    elif step == "interview_c_intro":
        indices = st.session_state.get("cq_indices", [])

        st.title("성향 질문 안내")

        if not indices:
            st.error("선택된 성향 질문이 없습니다. 성향 설문 단계로 돌아가 주세요.")
            if st.button("←"):
                goto("interview_dlcq")
        else:
            st.markdown(
                """
                방금 성향 설문에서 **'예'라고 응답하신 문항들** 중  
                세 가지를 선택하여 이번 검사에서 사용할 **성향 질문** 으로 구성합니다.

                성향 설문에서는 해당 문항들에 **'예'라고 답하셨지만**,  
                **성향 질문에서는 이 세 문항에 모두 '아니오'라고 답변**하셔야 합니다.

                다음 화면에서 선택된 세 문항을 그대로 다시 보여드리겠습니다.  
                각 문항을 읽어보시고,  
                **'예'라고 했던 내용을 '아니오'라고 말해보는 연습**을 하겠습니다.
                """
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("←"):
                    goto("interview_dlcq")
            with col2:
                if st.button("→"):
                    goto("interview_c_practice")

    # ---------- 10) C 연습 ----------
    elif step == "interview_c_practice":
        indices = st.session_state.get("cq_indices", [])
        st.title("성향 질문 연습")

        if not indices:
            st.error("선택된 성향 질문이 없습니다. 성향 설문 단계로 돌아가 주세요.")
            if st.button("성향 설문으로 돌아가기"):
                goto("interview_dlcq")
        else:
            all_answered = True
            all_correct = True

            for idx in indices:
                item = DLCQ_ITEMS[idx]
                ans = st.radio(
                    item,
                    ["선택 안 함", "예", "아니오"],
                    index=0,
                    key=f"cq_practice_{idx}",
                )
                if ans == "선택 안 함":
                    all_answered = False
                    all_correct = False
                elif ans != "아니오":
                    all_correct = False

            col1, col2 = st.columns(2)
            with col1:
                if st.button("←"):
                    goto("interview_c_intro")
            with col2:
                if st.button("→"):
                    if not all_answered:
                        st.error("세 문항 모두에 대해 '예' 또는 '아니오'를 선택해 주세요.")
                    elif not all_correct:
                        st.error("성향 질문은 모두 '아니오'로 연습해야 합니다.")
                    else:
                        goto("interview_n_intro")

    # ---------- 11) N 안내 ----------
    elif step == "interview_n_intro":
        st.title("인적 사항 질문 안내")

        st.markdown(
            """
            마지막으로, 피검자님의 인적 사항을 확인하는  
            **인적 사항 질문** 세 문항을 연습합니다.

            이름, 성별, 나이와 같이 사실 그대로의 정보를 묻는 질문입니다.  
            다음 화면에서 세 문항을 제시하고, 예/아니오 응답을 연습해 보겠습니다.
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_c_practice")
        with col2:
            if st.button("→"):
                goto("interview_n_practice")

    # ---------- 12) N 연습 ----------
    elif step == "interview_n_practice":
        info = st.session_state["case_info"]
        name = info["name"]
        gender = info["gender"]
        age = info["age"]

        st.title("인적 사항 질문 연습")

        n_questions = [
            f"당신의 이름은 {name} 입니까?",
            f"당신의 성별은 {gender} 입니까?",
            f"당신의 나이는 {age}세 입니까?",
        ]
        st.session_state["case_info"]["N_questions"] = n_questions

        all_answered = True
        all_correct = True

        for i, q in enumerate(n_questions, start=1):
            ans = st.radio(
                q,
                ["선택 안 함", "예", "아니오"],
                index=0,
                key=f"nq_{i}",
            )
            if ans == "선택 안 함":
                all_answered = False
                all_correct = False
            elif ans != "예":
                all_correct = False

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_n_intro")
        with col2:
            if st.button("→"):
                if not all_answered:
                    st.error("세 문항 모두에 대해 '예' 또는 '아니오'를 선택해 주세요.")
                elif not all_correct:
                    st.error("인적 사항 질문은 연습 단계에서 모두 '예'로 응답해야 합니다.")
                else:
                    # 최종 질문 세트 구성
                    info = st.session_state["case_info"]
                    r_set = info.get("R_questions", [])
                    n_set = n_questions
                    c_set = [DLCQ_ITEMS[i] for i in st.session_state["cq_indices"]]

                    st.session_state["question_set"] = {
                        "core_claim": info["core_claim"],
                        "I": I_QUESTION,
                        "SR": SR_QUESTION,
                        "N": n_set,
                        "C": c_set,
                        "R": r_set,
                    }
                    goto("interview_final_intro")

    # ---------- 13) 11문항 최종 연습 안내 ----------
    elif step == "interview_final_intro":
        st.title("최종 연습 안내")

        st.markdown(
            """
            이제 실제 검사에 앞서,  
            검사에서 진행될 **11가지 질문을 한 번에 연습**해 보겠습니다.

            다음 화면에서는 다음 순서대로 문항이 제시됩니다.

            1. 기초 질문 2문항
            2. 인적 사항 질문 3문항  
            3. 성향 질문 3문항
            4. 사건 관련 질문 3문항  

            실제 검사라고 생각하시고,  
            각 문항에 대해 차분히 **'예' 또는 '아니오'** 를 선택해 주세요.
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_n_practice")
        with col2:
            if st.button("→"):
                goto("interview_final_practice")

    # ---------- 14) 11문항 최종 연습 ----------
    elif step == "interview_final_practice":
        qs = st.session_state.get("question_set", None)
        info = st.session_state.get("case_info", {})
        role_key = info.get("role", "suspect")

        st.title("최종 연습")

        if not qs:
            st.error("질문 세트가 생성되지 않았습니다. 이전 단계로 돌아가 주세요.")
            if st.button("←"):
                goto("interview_final_intro")
        else:
            final_all_answered = True
            final_all_correct = True
            r_conflict = False

            # I / SR
            ans_I = st.radio(
                qs['I'],
                ["선택 안 함", "예", "아니오"],
                index=0,
                key="final_I",
            )
            if ans_I == "선택 안 함":
                final_all_answered = False
                final_all_correct = False
            elif ans_I != "예":
                final_all_correct = False

            ans_SR = st.radio(
                qs['SR'],
                ["선택 안 함", "예", "아니오"],
                index=0,
                key="final_SR",
            )
            if ans_SR == "선택 안 함":
                final_all_answered = False
                final_all_correct = False
            elif ans_SR != "예":
                final_all_correct = False

            # N (3)
            for i, q in enumerate(qs["N"], start=1):
                ans = st.radio(
                    q,
                    ["선택 안 함", "예", "아니오"],
                    index=0,
                    key=f"final_N_{i}",
                )
                if ans == "선택 안 함":
                    final_all_answered = False
                    final_all_correct = False
                elif ans != "예":
                    final_all_correct = False

            # C (3)
            for i, q in enumerate(qs["C"], start=1):
                ans = st.radio(
                    q,
                    ["선택 안 함", "예", "아니오"],
                    index=0,
                    key=f"final_C_{i}",
                )
                if ans == "선택 안 함":
                    final_all_answered = False
                    final_all_correct = False
                elif ans != "아니오":
                    final_all_correct = False

            # R (3) — 역할에 따라 기대 응답 다름
            for i, q in enumerate(qs["R"], start=1):
                ans = st.radio(
                    q,
                    ["선택 안 함", "예", "아니오"],
                    index=0,
                    key=f"final_R_{i}",
                )
                if ans == "선택 안 함":
                    final_all_answered = False
                    final_all_correct = False
                else:
                    expected = "아니오" if role_key == "suspect" else "예"
                    if ans != expected:
                        final_all_correct = False
                        r_conflict = True

            col1, col2 = st.columns(2)
            with col1:
                if st.button("←"):
                    goto("interview_final_intro")
            with col2:
                if st.button("→"):
                    if not final_all_answered:
                        st.error("11개 질문 모두에 대해 '예' 또는 '아니오'를 선택해 주세요.")
                    elif not final_all_correct:
                        # R 쪽에서의 충돌이면 별도 경고
                        if r_conflict:
                            if role_key == "suspect":
                                st.error(
                                    "사건 관련 질문에서 '예'라고 응답하면 가해 사실을 인정하는 것으로 해석됩니다. "
                                    "현재 응답은 검사의 전제와 맞지 않으므로, 검사관과 상의해 주세요."
                                )
                            else:
                                st.error(
                                    "사건 관련 질문에 대한 응답이 앞에서 입력한 피해 주장과 일치하지 않습니다. "
                                    "검사관과 상의해 주세요."
                                )
                        else:
                            st.error("Ophtheon 11문항은 설정된 규칙에 따라 응답해야 검사를 완료할 수 있습니다.")
                    else:
                        goto("interview_end")

    # ---------- 15) 면담 종료 + 프린트용 질문 세트 ----------
    elif step == "interview_end":
        qs = st.session_state.get("question_set", None)
        info = st.session_state.get("case_info", {})

        if not qs:
            st.error("질문 세트가 생성되지 않았습니다. 처음부터 다시 진행해 주세요.")
        else:
            core_claim = qs["core_claim"] if "core_claim" in qs else info.get("core_claim", "")

            st.success(
                """
                Ophtheon 검사 전 안내 및 연습이 모두 종료되었습니다.  

                아래에는 이번 검사에서 사용할 **최종 11문항 질문 세트**가 정리되어 있습니다.  
                이 내용을 출력하거나 파일로 저장하여, **검사관에게 제출**해 주세요.
                """
            )

            #st.markdown("### 1) 피검자의 핵심 주장")
            #st.info(core_claim)

            #st.markdown("### 2) 최종 11문항 질문 세트")

            # 화면에 보기 좋게 출력
            #st.markdown("**기초 질문**")
            #st.write(f"{qs['I']}")
            #st.write(f"{qs['SR']}")

            #st.markdown("**인적 사항 질문**")
            #for i, q in enumerate(qs["N"], start=1):
            #    st.write(f"{q}")

            #st.markdown("**성향 질문**")
            #for i, q in enumerate(qs["C"], start=1):
            #    st.write(f"{q}")

            #st.markdown("**사건 관련 질문**")
            #for i, q in enumerate(qs["R"], start=1):
            #   st.write(f"{q}")

            # 텍스트 파일로도 저장할 수 있게 구성
            lines = []
            lines.append("[피검자의 핵심 주장]")
            lines.append(core_claim)
            lines.append("")
            lines.append("[최종 11문항 질문 세트]")
            lines.append(f"I1. {qs['I']}")
            lines.append(f"SR1. {qs['SR']}")
            for i, q in enumerate(qs["N"], start=1):
                lines.append(f"N{i}. {q}")
            for i, q in enumerate(qs["C"], start=1):
                lines.append(f"C{i}. {q}")
            for i, q in enumerate(qs["R"], start=1):
                lines.append(f"R{i}. {q}")

            summary_text = "\n".join(lines)
            buffer = io.BytesIO(summary_text.encode("utf-8"))

            st.download_button(
                label="질문 다운로드 (.txt)",
                data=buffer,
                file_name="ophtheon_question_set.txt",
                mime="text/plain",
            )

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("←"):
                goto("interview_final_practice")
        with col2:
            if st.button("Home"):
                reset_all()


# ---------------------------------------------------------
# 모드: 데이터 업로드 & 자동 판정 (v0 간단 버전)
# ---------------------------------------------------------
elif mode == "upload":
    st.title("데이터 업로드 및 자동 판정 (v0)")

    st.markdown(
        """
        현재 v0 버전에서는 본 검사를 **별도의 검사자/아이트래커로 진행**한 뒤,  
        해당 세션의 동공 데이터(CSV)를 업로드하여 Ophtheon의 채점 로직을 테스트합니다.
        """
    )

    uploaded = st.file_uploader("동공 데이터 CSV 파일 업로드", type=["csv"])

    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.session_state["data"] = df
        st.write("데이터 미리보기:")
        st.dataframe(df.head())

        # v0: 아주 단순한 예시 점수
        if "D_RATIO" in df.columns:
            delta_example = round(df["D_RATIO"].max() - df["D_RATIO"].min(), 3)
            st.write(f"예시 Δ 값 (최대-최소): {delta_example}")
        else:
            st.warning("D_RATIO 컬럼이 없어 예시 Δ 값을 계산할 수 없습니다.")

    if st.button("Home"):
        reset_all()
