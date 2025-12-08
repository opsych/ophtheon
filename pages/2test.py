import streamlit as st
import random
import io
import re
import json
import tempfile
import os
from openai import OpenAI
client = OpenAI()

# ---------------------------------------------------------
# 0. OpenAI TTS: 텍스트 → mp3 파일 생성
# ---------------------------------------------------------
def generate_mp3_from_text(text: str) -> str:
    """OpenAI TTS로 텍스트를 mp3 파일로 저장하고, 파일 경로를 반환"""
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",   # 원하면 다른 목소리로 변경 가능
        input=text,
    )
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    # 응답 객체가 제공하는 메서드로 바로 파일로 저장
    response.stream_to_file(tmp_file.name)
    return tmp_file.name


def generate_all_question_mp3(seq):
    """
    seq = [ {"text": ...}, ... 11문항 ]
    각 질문 텍스트를 mp3로 변환한 파일 경로 리스트 반환
    """
    mp3_list = []
    for item in seq:
        q_text = item["text"]
        mp3_path = generate_mp3_from_text(q_text)
        mp3_list.append(mp3_path)
    return mp3_list


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

# TTS로 만든 mp3 파일들
if "exam_baseline_mp3" not in st.session_state:
    st.session_state["exam_baseline_mp3"] = None

if "exam_question_mp3" not in st.session_state:
    st.session_state["exam_question_mp3"] = None   # 11개 mp3 경로 리스트

# 검사 진행 상태
if "exam_phase" not in st.session_state:
    st.session_state["exam_phase"] = "baseline"    # "baseline" / "questions"

if "exam_q_index" not in st.session_state:
    st.session_state["exam_q_index"] = 0


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
**질문 세트 텍스트(.txt)** 파일을 업로드해 주세요.
        """
    )

    uploaded = st.file_uploader("질문 세트 텍스트 파일(.txt) 업로드", type=["txt"])

    if uploaded is not None:
        text = uploaded.read().decode("utf-8")
        core_claim, questions = parse_question_set_txt(text)
        seq = build_exam_sequence(questions)

        st.session_state["exam_core_claim"] = core_claim
        st.session_state["exam_questions"] = seq

        # OpenAI TTS로 baseline 안내 mp3 & 각 질문 mp3 생성
        baseline_text = "약 30초 이후 검사 질문이 시작됩니다. 질문과 질문 사이에는 15초의 대기시간이 있습니다."
        baseline_mp3 = generate_mp3_from_text(baseline_text)
        q_mp3_list = generate_all_question_mp3(seq)

        st.session_state["exam_baseline_mp3"] = baseline_mp3
        st.session_state["exam_question_mp3"] = q_mp3_list
        st.session_state["exam_phase"] = "baseline"
        st.session_state["exam_q_index"] = 0

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
- 그 이후, 각 문항 사이에는 **약 15초의 대기 시간**을 두고 음성이 재생됩니다.
(현재 버전에서는 대기시간은 검사관이 직접 맞춰주시면 됩니다.)
            """
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("다시 업로드하기"):
                st.session_state["test_step"] = "upload"
                st.rerun()
        with col2:
            if st.button("검사 시행으로 이동"):
                st.session_state["test_step"] = "run"
                st.session_state["exam_phase"] = "baseline"
                st.session_state["exam_q_index"] = 0
                st.rerun()

# ---------- (3) 실제 검사 화면 ----------
elif step == "run":
    seq = st.session_state.get("exam_questions", None)
    core_claim = st.session_state.get("exam_core_claim", "")
    baseline_mp3 = st.session_state.get("exam_baseline_mp3", None)
    q_mp3_list = st.session_state.get("exam_question_mp3", None)
    phase = st.session_state.get("exam_phase", "baseline")
    q_idx = st.session_state.get("exam_q_index", 0)

    if not seq or not q_mp3_list:
        st.error("질문 세트가 로드되지 않았습니다. 다시 업로드해 주세요.")
        if st.button("다시 업로드하기"):
            st.session_state["test_step"] = "upload"
            st.rerun()
    else:
        st.title("검사 시행 — 실시간 진행")

        # ---------------- 회색 화면 (십자 응시) ----------------
        st.markdown(
            """
<div style="
    background-color: rgb(125,125,125);
    border-radius:16px;
    padding:150px;
    text-align:center;
    min-height:60vh;
    margin-bottom:30px;
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

        # ---------------- 검사 단계 안내 + 오디오 ----------------
        if phase == "baseline":
            st.markdown(
                """
**1) 베이스라인 측정 단계 (약 30초)**  

- 위 십자(+)를 응시하면서,  
- 아래 음성을 재생한 뒤 **약 30초간** 정면 응시를 유지해 주세요.
                """
            )
            if baseline_mp3:
                st.audio(baseline_mp3)

            st.info("검사관: baseline 음성을 재생한 뒤, 약 30초 경과 후 '질문 시작' 버튼을 눌러주세요.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("← 질문 세트 확인으로 돌아가기"):
                    st.session_state["test_step"] = "preview"
                    st.rerun()
            with col2:
                if st.button("질문 시작 ➜"):
                    st.session_state["exam_phase"] = "questions"
                    st.session_state["exam_q_index"] = 0
                    st.rerun()

        elif phase == "questions":
            # 현재 질문 정보
            item = seq[q_idx]
            q_text = item["text"]
            q_audio = q_mp3_list[q_idx]

            st.markdown(
                f"""
**2) 질문 단계 — 문항 {q_idx + 1} / {len(seq)}**  

검사관은 아래 질문을 확인한 뒤,  
AI 음성을 함께 재생하여 피검자에게 들려주고,  
피검자의 육성 응답과 동공 반응을 관찰합니다.
                """
            )

            st.markdown(f"**질문 텍스트 (검사관용)**  \n{q_text}")

            st.audio(q_audio)

            st.info(
                """
검사관: 문항 음성을 재생한 뒤,  
피검자가 '예' 또는 '아니오'라고 대답하게 하고,  
약 15초의 간격을 두고 다음 문항으로 넘어가 주세요.
                """
            )

            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("← 이전 문항"):
                    if q_idx > 0:
                        st.session_state["exam_q_index"] = q_idx - 1
                        st.rerun()
                    else:
                        st.session_state["exam_phase"] = "baseline"
                        st.rerun()
            with col3:
                if st.button("다음 문항 →"):
                    if q_idx < len(seq) - 1:
                        st.session_state["exam_q_index"] = q_idx + 1
                        st.rerun()
                    else:
                        st.success("11문항 검사가 모두 종료되었습니다.")
                        if st.button("검사 종료"):
                            st.session_state["test_step"] = "upload"
                            st.session_state["exam_phase"] = "baseline"
                            st.session_state["exam_q_index"] = 0
                            st.rerun()
