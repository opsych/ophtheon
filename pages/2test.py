import streamlit as st
import re
import tempfile
from openai import OpenAI

client = OpenAI()

# ---------------------------------------------------------
# 0. TTS: 텍스트 → mp3 파일 하나 생성
# ---------------------------------------------------------
def generate_exam_mp3(full_script: str) -> str:
    """
    OpenAI TTS로 전체 검사 스크립트를 mp3 파일로 저장하고, 경로를 반환.
    """
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=full_script,
    )
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    response.stream_to_file(tmp_file.name)
    return tmp_file.name


# ---------------------------------------------------------
# 1. 스타일
# ---------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=Nanum+Gothic:wght@400;700&display=swap');

html, body {
    font-family: 'Sora', 'Nanum Gothic', sans-serif !important;
}

.block-container {
    font-size: 16px !important;
    line-height: 1.65 !important;
}

h1 { font-size: 30px !important; }
h2 { font-size: 26px !important; }
h3 { font-size: 22px !important; }
h4 { font-size: 18px !important; }

[data-testid="stSidebar"] * {
    font-size: 15px !important;
    line-height: 1.4 !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. 상태
# ---------------------------------------------------------
if "test_step" not in st.session_state:
    st.session_state["test_step"] = "upload"   # "upload" / "prepare" / "run"
if "exam_core_claim" not in st.session_state:
    st.session_state["exam_core_claim"] = ""
if "exam_questions" not in st.session_state:
    st.session_state["exam_questions"] = None
if "exam_full_audio" not in st.session_state:
    st.session_state["exam_full_audio"] = None


# ---------------------------------------------------------
# 3. 텍스트 파싱
# ---------------------------------------------------------
def parse_question_set_txt(text: str):
    """
    [피검자의 핵심 주장] / [최종 11문항 질문 세트] 형식의 txt에서
    core_claim, questions 딕셔너리 반환.
    """
    lines = [l.strip() for l in text.splitlines()]
    core_claim = ""
    questions = {"I": [], "SR": [], "N": [], "C": [], "R": []}

    for i, line in enumerate(lines):
        if line.startswith("[피검자의 핵심 주장]"):
            if i + 1 < len(lines):
                core_claim = lines[i + 1].strip()
            break

    pattern = re.compile(r"^(I\d+|SR\d+|N\d+|C\d+|R\d+)\.\s*(.+)$")
    for line in lines:
        m = pattern.match(line)
        if not m:
            continue
        code = m.group(1)
        question = m.group(2).strip()
        if code.startswith("SR"):
            qtype = "SR"
        else:
            qtype = code[0]
        questions[qtype].append(question)

    return core_claim, questions


def build_exam_sequence(questions: dict):
    """
    I, SR, N1 C1 R1, N2 C2 R2, N3 C3 R3 순서 시퀀스 생성.
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


def build_full_script(seq):
    """
    베이스라인 안내 + 11개 질문을 하나의 긴 한국어 스크립트로 생성.
    중간 타이밍은 말로 안내하는 방식.
    """
    # 베이스라인
    script_parts = []
    script_parts.append(
        "이제 옵시언 자동 검사를 시작하겠습니다. "
        "먼저 약 30초 동안 화면 중앙의 십자만 조용히 응시해 주세요. "
        "눈을 자주 깜빡이지 않도록 노력해 주시고, 몸을 움직이지 말아 주세요. "
        "그 후, 열한 개의 질문이 순서대로 재생됩니다. "
        "모든 질문에 대해 또렷한 목소리로 예 또는 아니오라고 대답해 주세요. "
    )

    # 질문 11개
    for i, item in enumerate(seq, start=1):
        q_text = item["text"]
        script_parts.append(
            f"\n\n이어서 잠시 후 질문을 드리겠습니다. "
            "질문이 끝난 후 삼 초 뒤, 예 또는 아니오라고 대답해 주세요. "
            f"잠시 후 다음 질문을 읽어 드리겠습니다. 천천히 내용을 들으신 뒤, 삼 초 안에 예 또는 아니오로 대답해 주세요. {q_text} . 사암, 이이, 일."
        )

    # 마지막 마무리
    script_parts.append(
        "\n\n이상으로 옵시언 자동 검사를 모두 마쳤습니다. "
        "십자 응시를 멈추시고 편안한 자세를 취하셔도 좋습니다."
    )

    full_script = " ".join(script_parts)
    return full_script


# ---------------------------------------------------------
# 4. 단계별 화면
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

        full_script = build_full_script(seq)

        st.markdown("질문 세트가 로드되었습니다. 이제 전체 검사 질문을 생성합니다.")

        with st.spinner("검사용 음성을 생성하고 있습니다. 잠시만 기다려 주세요..."):
            full_audio = generate_exam_mp3(full_script)

        st.session_state["exam_full_audio"] = full_audio
        st.session_state["test_step"] = "prepare"
        st.rerun()

# ---------- (2) 검사 전 안내 ----------
elif step == "prepare":
    full_audio = st.session_state.get("exam_full_audio", None)

    if not full_audio:
        st.error("검사용 질문이 준비되지 않았습니다. 다시 업로드해 주세요.")
        if st.button("다시 업로드하기"):
            st.session_state["test_step"] = "upload"
            st.rerun()
    else:
        st.title("검사 시행 — 안내")

        st.markdown(
            """
이제 Ophtheon 자동 검사가 시작됩니다.

화면에는 **회색 배경과 십자(+)만** 표시됩니다.  
오디오를 재생한 후, 중앙에 나타나는 십자를 응시해야 합니다.  
총 11개의 질문이 자동으로 재생됩니다.  

질문을 들을 때마다,  
**또렷한 목소리로 '예' 또는 '아니오'** 라고 대답해 주세요.
            """
        )

        st.warning("검사 시작 후에는 오디오를 중간에 멈추지 말고, 끝까지 그대로 재생해 주세요.")

        if st.button("검사 화면으로 이동"):
            st.session_state["test_step"] = "run"
            st.rerun()

        st.markdown("---")
        st.markdown("생성된 검사용 오디오를 미리 들어보고 싶다면 아래 플레이어를 사용할 수 있습니다.")
        st.audio(full_audio)

# ---------- (3) 실제 검사 화면 ----------
elif step == "run":
    full_audio = st.session_state.get("exam_full_audio", None)

    if not full_audio:
        st.error("검사용 질문이 준비되지 않았습니다. 다시 업로드해 주세요.")
        if st.button("다시 업로드하기"):
            st.session_state["test_step"] = "upload"
            st.rerun()
    else:
        st.title("검사 시행 — 자동 진행")

        # 회색 화면 + 십자 응시
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

        st.markdown(
            """
오디오를 재생하면, 검사 안내와 질문이 순서대로 제시됩니다.

검사 중에는 화면 중앙의 십자(+)를 계속 응시하면서,  
질문을 들을 때마다 또렷하게 **'예' 또는 '아니오'** 라고 대답해 주세요.
            """
        )

        st.audio(full_audio)

        st.markdown("---")
        if st.button("검사 종료"):
            st.session_state["test_step"] = "upload"
            st.session_state["exam_full_audio"] = None
            st.rerun()
