import streamlit as st
import random
import io
import re
import json

# ---------------------------------------------------------
# 1. 공통 스타일 (pretest와 동일 톤)
# ---------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Nanum+Gothic:wght@400;700&display=swap');

/* 전체 폰트 */
html, body {
    font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
}

/* 본문 영역 */
.block-container {
    font-size: 16px !important;
    line-height: 1.65 !important;
}

/* 제목 크기 */
h1 { font-size: 30px !important; }
h2 { font-size: 26px !important; }
h3 { font-size: 22px !important; }
h4 { font-size: 18px !important; }

/* 본문 UI 요소 */
.block-container .stRadio label,
.block-container .stRadio div,
.block-container .stCheckbox label,
.block-container .stTextInput input,
.block-container .stSelectbox div,
.block-container .stTextArea textarea,
.block-container .stSlider label,
.block-container .stSlider span,
.block-container .stAlert > div {
    font-size: 16px !important;
    line-height: 1.55 !important;
}

/* 사이드바 기본 */
[data-testid="stSidebar"] * {
    font-size: 15px !important;
    line-height: 1.4 !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. 상태 관리
# ---------------------------------------------------------
if "test_step" not in st.session_state:
    st.session_state["test_step"] = "upload"   # "upload" / "preview" / "run"

if "exam_core_claim" not in st.session_state:
    st.session_state["exam_core_claim"] = ""

if "exam_questions" not in st.session_state:
    st.session_state["exam_questions"] = None  # 11문항 순서 리스트

if "exam_started" not in st.session_state:
    st.session_state["exam_started"] = False


# ---------------------------------------------------------
# 3. 텍스트 파일 파싱 함수
# ---------------------------------------------------------
def parse_question_set_txt(text: str):
    """
    ophtheon_question_set.txt 형식의 텍스트를 파싱해서
    core_claim, questions 딕셔너리로 반환.
    questions = {"I": [...], "SR": [...], "N": [...], "C": [...], "R": [...]}
    """
    lines = [l.strip() for l in text.splitlines()]

    core_claim = ""
    questions = {"I": [], "SR": [], "N": [], "C": [], "R": []}

    # 핵심 주장 찾기
    for i, line in enumerate(lines):
        if line.startswith("[피검자의 핵심 주장]"):
            if i + 1 < len(lines):
                core_claim = lines[i + 1].strip()
            break

    # 질문 부분 파싱
    pattern = re.compile(r"^(I\d+|SR\d+|N\d+|C\d+|R\d+)\.\s*(.+)$")

    for line in lines:
        m = pattern.match(line)
        if not m:
            continue
        code = m.group(1)   # I1, SR1, N1, ...
        question = m.group(2).strip()

        if code.startswith("SR"):
            qtype = "SR"
        else:
            qtype = code[0]  # 'I', 'N', 'C', 'R'

        questions[qtype].append(question)

    return core_claim, questions


def build_exam_sequence(questions: dict):
    """
    questions 딕셔너리에서 Ophtheon용 11문항 한 세트 생성.

    순서 패턴:
        I, SR,
        N, C, R,
        N, C, R,
        N, C, R

    N/C/R은 각각 리스트 순서대로 1,2,3번 소비.
    """
    pattern = ["I", "SR", "N", "C", "R", "N", "C", "R", "N", "C", "R"]
    counters = {"I": 0, "SR": 0, "N": 0, "C": 0, "R": 0}
    seq = []

    for t in pattern:
        idx = counters[t]
        try:
            q_text = questions[t][idx]
        except IndexError:
            q_text = f"[{t} 질문이 부족합니다]"
        seq.append({"type": t, "index": idx + 1, "text": q_text})
        if t in ["N", "C", "R"]:
            counters[t] += 1

    return seq


# ---------------------------------------------------------
# 4. 화면 단계별 구성
# ---------------------------------------------------------
step = st.session_state["test_step"]

# ---------- (1) 텍스트 파일 업로드 ----------
if step == "upload":
    st.title("검사 시행 — 질문 세트 불러오기")

    st.markdown(
        """
pretest 단계에서 생성한  
텍스트(.txt) 파일을 업로드해 주세요.
        """
    )

    uploaded = st.file_uploader("질문 세트 텍스트 파일(.txt) 업로드", type=["txt"])

    if uploaded is not None:
        text = uploaded.read().decode("utf-8")
        core_claim, questions = parse_question_set_txt(text)
        seq = build_exam_sequence(questions)

        st.session_state["exam_core_claim"] = core_claim
        st.session_state["exam_questions"] = seq
        st.session_state["test_step"] = "preview"
        st.rerun()

# ---------- (2) 질문 세트 미리보기 ----------
elif step == "preview":
    seq = st.session_state.get("exam_questions", None)
    core_claim = st.session_state.get("exam_core_claim", "")

    if not seq:
        st.error("질문 세트가 로드되지 않았습니다. 다시 업로드해 주세요.")
        if st.button("다시 업로드하기"):
            st.session_state["test_step"] = "upload"
            st.rerun()
    else:
        st.title("검사 시행 — 질문 세트 확인")

        st.markdown("#### 피검자의 핵심 주장")
        st.info(core_claim)

        st.markdown("#### 이번 검사에서 사용할 11문항 순서")
        for i, item in enumerate(seq, start=1):
            tag = item["type"]
            idx = item["index"]
            st.write(f"{i}. [{tag}{idx}] {item['text']}")

        st.markdown(
            """
위 순서로 검사가 진행됩니다.  

- 검사 시작 후 **약 30초 동안은 베이스라인 측정 시간**입니다.  
- 그 이후, 각 문항 사이에는 **약 15초의 대기 시간**이 있습니다.
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("다시 업로드하기"):
                st.session_state["test_step"] = "upload"
                st.rerun()
        with col2:
            if st.button("검사 시행"):
                st.session_state["test_step"] = "run"
                st.session_state["exam_started"] = False
                st.rerun()

# ---------- (3) 실제 검사 화면 ----------
# ---------- (3) 실제 검사 화면 ----------
elif step == "run":
    seq = st.session_state.get("exam_questions", None)
    core_claim = st.session_state.get("exam_core_claim", "")

    if not seq:
        st.error("질문 세트가 로드되지 않았습니다. 다시 업로드해 주세요.")
        if st.button("다시 업로드하기"):
            st.session_state["test_step"] = "upload"
            st.session_state["exam_started"] = False
            st.rerun()
    else:
        st.title("검사 시행 — 실시간 진행")

        exam_started = st.session_state.get("exam_started", False)

        # 시작 전 안내 텍스트
        if not exam_started:
            st.markdown(
                """
AI 검사관의 안내에 따라 **정면을 응시**하고,  
각 문항에 대해 육성으로 '예' 또는 '아니오'라고 답변해 주세요.
                """
            )

        # ---------------- 회색 화면 ----------------
        if not exam_started:
            # 시작 전: 설명 텍스트가 있는 연한 회색 박스
            st.markdown(
                """
<div style="
    background-color:#f2f2f2;
    border-radius:16px;
    padding:160px 120px;
    text-align:center;
    min-height:300px;
    display:flex;
    flex-direction:column;
    justify-content:center;">
  <div style="font-size:22px; font-weight:500; margin-bottom:12px;">
    검사 시작 버튼을 누르면 안내 음성이 재생되고,  
    약 30초 후 첫 번째 질문이 시작됩니다.
  </div>
  <div style="font-size:15px; color:#555555;">
    이 시간 동안에는 정면을 바라보며 편안하게 호흡해 주세요.
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # 검사 시작 후: 진짜 검사 화면 (125,125,125 회색 + 십자)
            st.markdown(
                """
<div style="
    background-color: rgb(125,125,125);
    border-radius:16px;
    padding:160px 120px;
    text-align:center;
    min-height:300px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;">
  <div style="font-size:72px; font-weight:700; color:#000000;">
    +
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )

        # ---------------- 버튼 영역 ----------------
        col1, col2 = st.columns(2)
        with col1:
            if st.button("돌아가기"):
                st.session_state["test_step"] = "preview"
                st.session_state["exam_started"] = False
                st.rerun()

        with col2:
            # 시작 전에는 "검사 시작" 버튼 표시, 시작 후에는 숨김
            if not exam_started:
                if st.button("검사 시작"):
                    st.session_state["exam_started"] = True
                    st.rerun()

        # ---------------- 검사 시작 후: JS TTS 스케줄링 ----------------
        if exam_started:
            # 질문 텍스트 배열
            question_texts = [item["text"] for item in seq]

            # Python 리스트 → JS용 JSON 문자열
            questions_js = json.dumps(question_texts, ensure_ascii=False)

            st.markdown(
                f"""
<script>
const questions = {questions_js};
const baselineMs = 30000;  // 30초 베이스라인
const gapMs = 15000;       // 문항 사이 15초 대기

function speak(text) {{
    try {{
        window.speechSynthesis.cancel();  // 이전 음성 중단
        var msg = new SpeechSynthesisUtterance(text);
        msg.lang = "ko-KR";
        window.speechSynthesis.speak(msg);
    }} catch (e) {{
        console.log(e);
    }}
}}

// 검사 안내 음성 (baseline 시작)
speak("약 30초 이후 검사 질문이 시작됩니다. 질문과 질문 사이에는 15초의 대기시간이 있습니다.");

// 30초 대기 후 첫 번째 질문, 이후 15초 간격으로 다음 질문
let t = baselineMs;

questions.forEach((q, idx) => {{
    setTimeout(() => {{
        speak(q);
    }}, t);
    t += gapMs;
}});
</script>
                """,
                unsafe_allow_html=True,
            )
