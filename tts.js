/**
 * TTS (텍스트 음성 변환) 및 ON/OFF 버튼 관리 파일 (고객용)
 *
 * [서버 주소 변경 방법]
 * 핫스팟 환경이나 외부 접속(ngrok) 환경에 맞게 아래 주소 중 하나만 활성화(주석 해제)하여 사용하세요.
 */

// 1. 같은 장치 테스트용
// const SERVER_URL = "http://127.0.0.1:5000";

// 2. 라즈베리파이 내부 IP 주소용 (기존 동작 환경)
const SERVER_URL = "http://192.168.47.80:5000";

// 3. 외부 접속 / ngrok 도메인용 (예시)
// const SERVER_URL = "https://xxxxx.ngrok-free.app";

// 로컬스토리지 기반 상태 관리
function isTtsEnabled() {
  // 기본값은 OFF(false)
  return localStorage.getItem("tts_enabled") === "true";
}

function toggleTts() {
  const newState = !isTtsEnabled();
  localStorage.setItem("tts_enabled", newState ? "true" : "false");
  updateButtonUI();

  if (newState) {
    // 켜졌을 때 즉시 피드백 안내
    speakText("음성 안내 서비스가 시작되었습니다.");
  }
}

// TTS 실행 함수
function speakText(text) {
  // 1. 사용자 활성화 여부 체크
  if (!isTtsEnabled()) return;

  // 2. 브라우저 음성 엔진 정지 (밀림 방지)
  if (speechSynthesis.speaking) {
    speechSynthesis.cancel();
  }

  // 3. 음성 생성 및 재생
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "ko-KR";
  utterance.rate = 0.9; // 살짝 천천히 (어르신 배려)

  speechSynthesis.speak(utterance);
}

// UI 동적 주입 (상단 고정 버튼)
function injectTtsButton() {
  // 중복 주입 방지
  if (document.getElementById("fixed-tts-button")) return;

  const btn = document.createElement("button");
  btn.id = "fixed-tts-button";

  // 기본 스타일 지정 (어르신용: 크고 굵은 글씨, 높은 대비)
  Object.assign(btn.style, {
    position: "fixed",
    top: "0",
    left: "0",
    width: "100%",
    height: "80px",
    zIndex: "9999",
    border: "none",
    borderBottom: "4px solid #000",
    fontFamily: "inherit",
    fontSize: "28px",
    fontWeight: "900",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
    transition: "all 0.2s ease",
    boxSizing: "border-box",
  });

  btn.onclick = (e) => {
    // 이벤트 버블링(화면 클릭 등) 전파 방지
    e.stopPropagation();
    toggleTts();
  };

  // 바디 영역 패딩 추가 (화면 컨텐츠가 가려지지 않게 아래로 밀기)
  document.body.style.paddingTop = "80px";

  // 바디 최상단에 삽입
  document.body.prepend(btn);

  // 초기 UI 상태 갱신
  updateButtonUI();
}

function updateButtonUI() {
  const btn = document.getElementById("fixed-tts-button");
  if (!btn) return;

  const active = isTtsEnabled();

  if (active) {
    // 활성화 상태: 눈에 띄는 초록색/노란색 테마 추천. 여기선 직관적인 대비 테마 사용
    btn.innerHTML =
      '<span style="font-size: 36px; margin-right: 15px;">🔊</span> 음성 안내 켜져 있음 (끄려면 누르세요)';
    btn.style.backgroundColor = "#22c55e"; // 초록색
    btn.style.color = "#ffffff";
  } else {
    // 비활성화 상태: 경고/대기 시각 테마
    btn.innerHTML =
      '<span style="font-size: 36px; margin-right: 15px;">🔇</span> 음성 안내 꺼짐 (켜려면 누르세요)';
    btn.style.backgroundColor = "#374151"; // 진회색
    btn.style.color = "#ffffff";
  }
}

// 태그 실시간 감지 폴링
let lastTagId = "";

async function pollLatestTag() {
  try {
    const response = await fetch(`${SERVER_URL}/latest-tag`);
    if (!response.ok) return;

    const data = await response.json();
    const currentTag = data.tag_id;

    // 새로운 태그 감지 시
    if (currentTag && currentTag !== lastTagId) {
      lastTagId = currentTag;
      console.log("[TTS] 새 태그 인식됨:", currentTag);

      // 즉각 발화 실행 (함수 내부에서 ON/OFF 상태 체크함)
      speakText("상품이 추가되었습니다.");
    }
  } catch (error) {
    // 주기적 폴링 실패 시 에러 폭탄 방지를 위해 콘솔에만 가끔 출력하거나 패스
  }
}

// 초기 구동
// DOM이 완전히 준비되면 실행
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTtsSystem);
} else {
  initTtsSystem();
}

function initTtsSystem() {
  // 1. 버튼 주입
  injectTtsButton();

  // 2. 0.5초마다 스캔 실행
  setInterval(pollLatestTag, 500);
}
