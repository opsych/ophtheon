import streamlit as st
import random
import io
import re
import tempfile
import wave
from typing import List

from openai import OpenAI

client = OpenAI()

# ---------------------------------------------------------
# 0. OpenAI TTS: 텍스트 → WAV 파일 생성
# ---------------------------------------------------------
def generate_tts_wav(text: str) -> str:
    """
    OpenAI TTS로 텍스트를 WAV 파일로 저장하고, 파일 경로를 반환.
    """
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",   # 다른 목소리로 바꾸고 싶으면 여기만 수정
        input=text,
        response_format="wav",
    )
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    response.stream_to_file(tmp_file.name)
    return tmp_file.name


def concat_with_silence(wav_paths: List[str], silence_secs: List[float]) -> str:
    """
    여러 WAV 파일을 순서대로 이어 붙이고, 각 파일 뒤에 지정한 길이(초)의 무음을 삽입.
    - wav_paths: [baseline, q1, q2, ..., q11]
    - silence_secs: [30, 15, 15, ..., 0]  (각 세그먼트 뒤 무음 길이)
    """
    assert len(wav_paths) == len(silence_secs), "wav_paths와 silence_secs 길이가 같아야 합니다."

    # 기준 파라미터 얻기 (모든 TTS 출력이 같은 포맷이라고 가정)
    with wave.open(wav_paths[0], "rb") as w:
        params = w.getparams()
        nchannels, sampwidth, framerate, nframes = params[:4]

    def silence_bytes(seconds: float) -> bytes:
        n_samples = int(framerate * seconds)
        return b"\x00" * n_samples * nchannels * sampwidth

    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    with wave.open(out_path, "wb") as out_w:
        out_w.setparams(params)

        for idx, path in enumerate(wav_paths):
            with wave.open(path, "rb") as w:
                data = w.readframes(w.getnframes())
            out_w.writeframes(data)

            sil_sec = silence_secs[idx]
            if sil_sec > 0:
                out_w.writeframes(silence_bytes(sil_sec))

    return out_path


def generate_full_exam_wav(seq: List[dict]) -> str:
    """
    11문항 시퀀스를 받아서:
    - 베이스라인 안내 멘트 + 질문 11개를 TTS WAV로 만들고
    - 베이스라인 뒤 30초, 각 질문 뒤 15초(마지막은 0초) 무음을 삽입해
      하나의 연속 WAV 파일을 생성하여 경로를 반환.
    """
    # 1) 베이스라인 멘트
    baseline_text = (
        "이제 자동 검사가 시작됩니다. "
        "지금부터 30초 동안은 화면 중앙의 십자를 조용히 응시하면서 눈을 깜빡이지 않도록 해 주세요. "
        "30초가 지난 뒤, 열한 개의 질문이 순서대로 재생됩니다. "
        "각 질문 사이에는 약 15초의 간격이 있습니다. "
        "질문을 들을 때마다, 또렷한 목소리로 예 또는 아니오라고 대답해 주세요."
    )
    baseline_wav = generate_tts_wav(baseline_text)

    # 2) 각 질문을 TTS WAV로 생성
    question_wavs = [generate_tts_wav(item["text"]) for item in seq]

    # 3) 모든 세그먼트를 하나의 리스트로
    all_wavs = [baseline_wav] + question_wavs

    # 4) 각 세그먼트 뒤 넣을 무음 길이 (초)
    #    - baseline 뒤 30초
    #    - 각 질문 뒤 15초, 마지막 질문 뒤는 0초
    silence_secs = [30.0] + [15.0] * len(question_wavs)
    silence_secs[-1] = 0.0  # 마지막 질문 뒤에는 무음 없음

    # 5) WAV 이어 붙이고 최종 경로 반환
    full_wav_path = concat_with_silence(all_wavs, silence_secs)
    return full_wav_path


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
    st.session_state["test_step"] = "upload"   # "upload" / "prepare" / "run"

if "exam_core_claim" not in st.session_state:
    st.session_state["exam_core_claim"] = ""

if "exam_questions" not in st.session_state:
    st.session_state["exam_questions"] = None  # 11문항 시퀀스

# 하나의 긴 WAV 파일 경로
if "exam_full_audio" not in st.session_state:
    st.session_state["exam_full_audio"] = None


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

        st.markdown("질문 세트가 로드되었습니다. 이제 검사용 음성을 생성합니다.")

        with st.spinner("검사용 음성을 생성하고 있습니다. 잠시만 기다려 주세요..."):
            full_audio = generate_full_exam_wav(seq)

        st.session_state["exam_full_audio"] = full_audio
        st.session_state["test_step"] = "prepare"
        st.rerun()

# ---------- (2) 검사 전 요약 안내 ----------
elif step == "prepare":
    seq = st.session_state.get("exam_questions", None)
    full_audio = st.session_state.get("exam_full_audio", None)

    if not seq or not full_audio:
        st.error("질문 세트 또는 음성 파일이 준비되지 않았습니다. 다시 업로드해 주세요.")
        if st.button("다시 업로드하기"):
            st.session_state["test_step"] = "upload"
            st.rerun()
    else:
        st.title("검사 시행 — 안내")

        st.markdown(
            """
이제 Ophtheon 자동 검사가 시작됩니다.

- 화면에는 **회색 배경과 십자(+)만** 표시됩니다.  
- 오디오를 재생하면,  
  - 처음 약 30초 동안은 아무 질문 없이 십자를 응시하는 **베이스라인 구간**이 이어지고  
  - 그 이후, 총 11개의 질문이 자동으로 재생됩니다.  
- 각 질문 사이에는 약 15초의 간격이 포함되어 있습니다.  

피검자는 오디오에서 질문을 들을 때마다,  
**또렷한 목소리로 '예' 또는 '아니오'** 라고 대답하면 됩니다.
            """
        )

        st.warning("검사 시작 후에는 오디오를 중간에 멈추지 말고, 끝까지 그대로 재생해 주세요.")

        if st.button("검사 화면으로 이동"):
            st.session_state["test_step"] = "run"
            st.rerun()

        st.markdown("---")
        st.markdown("연구자용: 생성된 검사용 오디오를 미리 들어보고 싶다면 아래 플레이어를 사용할 수 있습니다.")
        st.audio(full_audio)

# ---------- (3) 실제 검사 화면 ----------
elif step == "run":
    full_audio = st.session_state.get("exam_full_audio", None)

    if not full_audio:
        st.error("검사용 음성이 준비되지 않았습니다. 다시 업로드해 주세요.")
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
오디오를 재생하면,  
**베이스라인 → 11개 질문 → 각 질문 사이의 무음**이  
순서대로 자동으로 이어집니다.

검사 중에는 화면 중앙의 십자(+)를 계속 응시하면서,  
질문을 들을 때마다 또렷하게 **'예' 또는 '아니오'** 라고 대답해 주세요.
            """
        )

        st.audio(full_audio)

        st.markdown("---")
        if st.button("검사 종료 후 처음으로 돌아가기"):
            st.session_state["test_step"] = "upload"
            st.session_state["exam_full_audio"] = None
            st.rerun()
