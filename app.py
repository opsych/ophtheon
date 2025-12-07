import streamlit as st
import pandas as pd
import random

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
    /* Google Fonts: Sora + Nanum Gothic 로드 */
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Nanum+Gothic:wght@400;700&display=swap');

    /* 전체 기본 폰트: 영문은 Sora, 한글은 Nanum Gothic */
    html, body, [class*="css"] {
        font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
        font-weight: 600 !important;
    }

    .stButton button,
    .stTextInput>div>div>input,
    .stSelectbox div,
    .stRadio label,
    .stCheckbox label,
    .stTextArea textarea {
        font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
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
    for key in ["mode", "step", "case_info", "dlcq_answers", "cq_indices", "question_set", "data"]:
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
        f"당신은 그 당시 피해자에게 {offense_text}을/를 가한 사실이 있습니까?",
        f"당신은 피해자를 {offense_text}한 적이 있습니까?",
        f"당신이 피해자에게 {offense_text}을/를 한 것이 사실입니까?",
    ]


def make_r_questions_victim(offense_text: str) -> list[str]:
    return [
        f"당신은 그 당시 피의자로부터 {offense_text}을/를 당한 사실이 있습니까?",
        f"당신은 피의자에게 직접 {offense_text}을/를 당한 적이 있습니까?",
        f"당신은 피의자로부터 {offense_text} 피해를 입은 것이 사실입니까?",
    ]


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
    # 홈에서만 상단 여백 조금 추가
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

    st.write("")
    st.markdown("#### 사용할 기능을 선택해 주세요.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("① 사전 면담 및 질문 생성", use_container_width=True):
            st.session_state["mode"] = "interview"
            st.session_state["step"] = "interview_info"
            st.rerun()
    with col2:
        if st.button("② 데이터 업로드 및 자동 판정", use_container_width=True):
            st.session_state["mode"] = "upload"
            st.session_state["step"] = "upload"
            st.rerun()

    st.write("")
    st.caption("© 2025 QnFP Lab · Jung Joo Lee")


# ---------------------------------------------------------
# 모드: 사전 면담 & 질문 생성
# ---------------------------------------------------------
elif mode == "interview":

    # ---------- 1) 정보 입력 (역할 + 사건유형 + 기본정보) ----------
    if step == "interview_info":
        st.title("1. 정보 입력 (역할 · 사건 정보)")

        role = st.radio(
            "이번 사건에서 본인의 위치를 선택해 주세요.",
            ["피의자", "피해자"],
            horizontal=True,
        )
        role_key = "suspect" if role == "피의자" else "victim"

        offense_category = st.selectbox(
            "사건의 대분류를 선택해 주세요.",
            [
                "성범죄",
                "폭력범죄",
                "재산범죄",
                "공무원범죄",
                "사이버범죄",
                "음주운전·교통범죄",
                "성매매",
                "마약",
                "기타",
            ],
        )

        # 대분류에 따른 세부유형 예시 (v0: 간단)
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
        else:
            offense_type = st.selectbox(
                "사건의 세부유형을 선택해 주세요.",
                ["기타"],
            )

        offense_free = ""
        if offense_type == "기타":
            offense_free = st.text_input(
                "어떤 행위에 관한 사건인지 간단히 적어주세요.",
                placeholder="예) 금품을 갈취, 사기 판매, 집에 침입, ...",
            )

        # 최종 텍스트 (템플릿에 들어갈 표현)
        if offense_type == "기타":
            offense_text = offense_free.strip() if offense_free else "행위를"
        else:
            offense_text = offense_type

        st.markdown("---")
        st.markdown("### 기본 인적 사항")

        name = st.text_input("이름 또는 피검자 ID")
        gender = st.radio("성별", ["남", "여", "기타"], horizontal=True)
        age = st.number_input("나이", min_value=18, max_value=80, value=25, step=1)

        agree = st.radio("검사 진행에 동의하십니까?", ["동의함", "동의하지 않음"], horizontal=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅︎ 처음으로 돌아가기"):
                reset_all()
        with col2:
            if st.button("다음 단계로 ➜"):
                if agree != "동의함":
                    st.error("검사에 동의하지 않으면 검사를 진행할 수 없습니다.")
                elif not name or not offense_text:
                    st.error("이름과 사건 정보는 반드시 입력해 주세요.")
                else:
                    # core_claim 자동 생성 (역할에 따라)
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
                    st.session_state["step"] = "interview_intro"
                    st.rerun()

    # ---------- 2) 인사 + 목적 설명 ----------
    elif step == "interview_intro":
        info = st.session_state["case_info"]
        name = info.get("name", "(이름 미지정)")

        st.title("2. 사전 면담 — 검사 목적 안내")

        st.markdown(
            f"""
            피검자 **{name}** 님, 안녕하세요.  
            지금부터 Ophtheon 검사의 목적과 절차를 간단히 설명드리겠습니다.

            이 검사는 법정에서 증거능력을 가지는 조사는 아니며,  
            동공 반응을 이용해 정서적 각성도와 반응 패턴을 확인하는 *스크리닝 용도*입니다.

            검사는 총 **11가지 질문**으로 구성되며,  
            지금부터 그 절차와 원리를 순서대로 안내드리겠습니다.
            """
        )

        if st.button("검사 원리 설명 듣기 ➜"):
            goto("interview_principle")

        if st.button("⬅︎ 정보 입력으로 돌아가기"):
            goto("interview_info")

    # ---------- 3) 검사 원리 설명 ----------
    elif step == "interview_principle":
        st.title("3. 검사 원리 설명")

        st.info(
            """
            누구나 살아오면서 한 번쯤 거짓말을 해본 경험이 있을 것입니다.  
            사람이 거짓말을 할 때는 죄책감, 불안, 긴장감, 속이는 즐거움 등의 다양한 감정을 느끼며  
            이러한 감정은 자율신경계의 생리적 반응을 유발합니다.

            특히, 심리적으로 중요한 질문을 듣거나 거짓을 말할 때  
            동공이 무의식적으로 조금 더 커지며, 이는 의도적으로 통제하기 어렵습니다.

            Ophtheon은 이러한 동공 반응을 질문 유형별로 기록하여,  
            비교질문(C)에 비해 사건 관련 질문(R)에서 반응이 더 큰지,  
            그 차이(ΔC–ΔR)를 AI 기반 자동 채점 알고리즘으로 분석합니다.
            """
        )

        if st.button("사건 관련 질문 안내 보기 ➜"):
            goto("interview_r_preview")

        if st.button("⬅︎ 이전 단계로"):
            goto("interview_intro")

    # ---------- 4) 사건 관련 R 질문 안내 ----------
    elif step == "interview_r_preview":
        info = st.session_state["case_info"]
        role_key = info["role"]
        offense_text = info["offense_text"]
        core_claim = info["core_claim"]

        st.title("4. 사건 관련 질문 안내 (R 질문)")

        st.markdown("#### 피검자의 핵심 주장")
        st.info(core_claim)

        st.markdown(
            """
            지금부터 **사건과 직접 관련된 질문(관련 질문, R)** 을 안내해 드리겠습니다.

            이 질문들은 피검자님의 주장과 관련된 **핵심 질문 3개**로 구성됩니다.  
            다음 화면에서 실제 질문 내용을 확인하고,  
            각 질문에 대해 연습 삼아 '예' 또는 '아니오'를 선택해 보게 됩니다.
            """
        )

        # 역할에 따라 R 질문 세트 생성
        if role_key == "suspect":
            r_questions = make_r_questions_suspect(offense_text)
        else:
            r_questions = make_r_questions_victim(offense_text)

        # 질문 세트 저장
        st.session_state["case_info"]["R_questions"] = r_questions

        if st.button("사건 관련 질문 확인 및 연습하기 ➜"):
            goto("interview_r_practice")

        if st.button("⬅︎ 검사 원리 설명으로"):
            goto("interview_principle")

    # ---------- 4-2) 사건 관련 R 질문 내용 + 연습 ----------
    elif step == "interview_r_practice":
        info = st.session_state["case_info"]
        r_questions = info.get("R_questions", [])

        st.title("4-2. 사건 관련 질문 내용 확인 및 연습")

        if not r_questions:
            st.error("사건 관련 질문이 생성되지 않았습니다. 이전 단계로 돌아가 주세요.")
            if st.button("⬅︎ 사건 관련 질문 안내로 돌아가기"):
                goto("interview_r_preview")
        else:
            st.markdown(
                """
                아래는 이번 검사에서 사용할 **사건 관련 질문(R)** 3개입니다.  

                실제 검사에서는 각 질문에 대해  
                본인의 상황에 따라 **'예' 또는 '아니오'** 로 답변하게 됩니다.

                지금은 연습 단계이므로,  
                각 질문에 대해 스스로 생각해 보고 **직접 선택**해 주세요.
                """
            )

            all_answered = True

            for i, q in enumerate(r_questions, start=1):
                ans = st.radio(
                    f"R{i}. {q}",
                    ["선택 안 함", "예", "아니오"],
                    key=f"r_practice_{i}",
                    index=0,  # 기본값: '선택 안 함'
                )
                if ans == "선택 안 함":
                    all_answered = False

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅︎ 사건 관련 질문 안내로 돌아가기"):
                    goto("interview_r_preview")
            with col2:
                if st.button("성향 설문(비교질문 후보)으로 ➜"):
                    if not all_answered:
                        st.error("모든 사건 관련 질문에 대해 '예' 또는 '아니오'를 선택해 주세요.")
                    else:
                        goto("interview_dlcq")

    # ---------- 5) 성향 설문 (DLCQ) ----------
    elif step == "interview_dlcq":
        st.title("5. 성향 설문 (비교질문 후보 생성)")

        st.markdown(
            """
            아래 질문들에는 솔직하게 '예' 또는 '아니오'로 응답해 주시면 됩니다.  
            검사에서는 이 중 일부 문항이 비교질문(C)으로 사용될 수 있습니다.
            (처음에는 모두 **'응답 안 함'** 으로 되어 있으니, 각 문항마다 직접 선택해 주세요.)
            """
        )

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
            if st.button("⬅︎ 사건 관련 질문 연습으로 돌아가기"):
                goto("interview_r_practice")
        with col2:
            if st.button("비교질문 연습으로 ➜"):
                if not any(answers.values()):
                    st.error("적어도 한 문항 이상 '예'로 응답해야 비교질문을 만들 수 있습니다.")
                else:
                    cq_indices = pick_cq_indices(answers, k=3)
                    st.session_state["cq_indices"] = cq_indices
                    goto("interview_cq_practice")

    # ---------- 6) 비교질문(C) 연습 ----------
    elif step == "interview_cq_practice":
        indices = st.session_state.get("cq_indices", [])
        if not indices:
            st.error("선택된 비교질문이 없습니다. 성향 설문 단계로 돌아가 주세요.")
            if st.button("성향 설문으로 돌아가기"):
                goto("interview_dlcq")
        else:
            st.title("6. 비교질문(C) 연습")

            st.markdown(
                """
                방금 '예'라고 응답하신 문항들 중 일부는 검사에서 **비교질문(C)** 으로 사용됩니다.  

                그러나 **본 검사에서는**, 이러한 질문들에 대해서도  
                모두 **'아니오'** 라고 답변해 주셔야 합니다.

                아래 세 가지 질문에 대해 연습 삼아 각 문항을 읽고,  
                스스로 생각한 뒤 **직접 '아니오'를 선택**해 주세요.
                """
            )

            all_no = True
            for idx in indices:
                item = DLCQ_ITEMS[idx]
                ans = st.radio(
                    item,
                    ["선택 안 함", "예", "아니오"],
                    key=f"cq_practice_{idx}",
                    index=0,  # 기본값: '선택 안 함'
                )
                if ans != "아니오":
                    all_no = False

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅︎ 성향 설문으로 돌아가기"):
                    goto("interview_dlcq")
            with col2:
                if st.button("인적 사항 질문 연습으로 ➜"):
                    if not all_no:
                        st.error("모든 비교질문에 대해 '아니오'를 선택해야 다음 단계로 진행할 수 있습니다.")
                    else:
                        goto("interview_nq_practice")

    # ---------- 7) 인적사항 N 질문 연습 ----------
    elif step == "interview_nq_practice":
        info = st.session_state["case_info"]
        name = info["name"]
        gender = info["gender"]
        age = info["age"]

        st.title("7. 인적 사항 질문(N) 연습")

        n_questions = [
            f"당신의 이름은 {name} 입니까?",
            f"당신의 성별은 {gender} 입니까?",
            f"당신의 나이는 {age}세 입니까?",
        ]
        st.session_state["case_info"]["N_questions"] = n_questions

        st.markdown(
            """
            이제 본 검사에 포함될 **중립 질문(N)** 을 연습해보겠습니다.  

            아래 질문들은 모두 **사실 그대로** 묻는 질문이므로,  
            실제 검사에서는 모두 **'예'라고 답변**해 주셔야 합니다.

            각 문항을 읽고 스스로 확인한 뒤,  
            직접 **'예'를 선택**해 주세요.
            """
        )

        all_yes = True
        for i, q in enumerate(n_questions):
            ans = st.radio(
                q,
                ["선택 안 함", "예", "아니오"],
                key=f"nq_{i}",
                index=0,  # 기본값: '선택 안 함'
            )
            if ans != "예":
                all_yes = False

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅︎ 비교질문 연습으로"):
                goto("interview_cq_practice")
        with col2:
            if st.button("질문 세트 요약 보기 ➜"):
                if not all_yes:
                    st.error("모든 중립 질문에 대해 '예'를 선택해야 다음 단계로 진행할 수 있습니다.")
                else:
                    # 최종 질문 세트 구성
                    info = st.session_state["case_info"]
                    r_set = info.get("R_questions", [])
                    c_set = [DLCQ_ITEMS[i] for i in st.session_state["cq_indices"]]
                    n_set = n_questions
                    attitude = [
                        "당신은 오늘 검사관과 연습한 것만 질문한다는 것을 믿습니까?",
                        "당신은 오늘 검사관이 묻는 질문에 사실대로 대답하겠습니까?",
                    ]
                    st.session_state["question_set"] = {
                        "core_claim": info["core_claim"],
                        "attitude": attitude,
                        "R": r_set,
                        "C": c_set,
                        "N": n_set,
                    }
                    goto("interview_summary")

    # ---------- 8) 최종 질문 세트 요약 ----------
    elif step == "interview_summary":
        qs = st.session_state.get("question_set", None)
        info = st.session_state["case_info"]

        st.title("8. 최종 질문 세트 요약 (연구자/검사관용)")

        if not qs:
            st.error("질문 세트가 생성되지 않았습니다. 처음부터 다시 진행해 주세요.")
        else:
            st.markdown("### 피검자의 핵심 주장")
            st.info(qs["core_claim"])

            st.markdown("### 태도 질문 (2)")
            for i, q in enumerate(qs["attitude"], start=1):
                st.write(f"T{i}. {q}")

            st.markdown("### 사건 관련 질문 R (3)")
            for i, q in enumerate(qs["R"], start=1):
                st.write(f"R{i}. {q}")

            st.markdown("### 비교 질문 C (3)")
            for i, q in enumerate(qs["C"], start=1):
                st.write(f"C{i}. {q}")

            st.markdown("### 중립 질문 N (3)")
            for i, q in enumerate(qs["N"], start=1):
                st.write(f"N{i}. {q}")

            st.info(
                """
                위 11개 문항(태도 2, 사건관련 3, 비교 3, 중립 3)은  
                Ophtheon 프로토콜에 따라 본 검사에서 사용될 질문 세트입니다.
                검사관은 위 순서 또는 사전에 정의한 순서로 질문을 제시할 수 있습니다.
                """
            )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅︎ 인적사항 연습 단계로 돌아가기"):
                goto("interview_nq_practice")
        with col2:
            if st.button("처음으로 돌아가기 ⟳"):
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

    if st.button("⬅︎ 홈으로 돌아가기"):
        reset_all()
