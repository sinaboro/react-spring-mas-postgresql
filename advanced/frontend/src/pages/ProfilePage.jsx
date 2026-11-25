// ProfilePage.jsx - (심화) 내 정보 · 닉네임 바꾸기 ( /me )
//
// 이 파일이 보여 주는 것
//   - 닉네임을 바꾸면 PUT /api/auth/me → 게이트웨이 → user-service (userdb 의 users 를 고친다)
//   - 그러면 내가 예전에 쓴 글의 작성자도 바뀔까?
//       Kafka 가 꺼져 있으면(app.kafka.enabled=false) → 안 바뀐다. posts.writer 는 복사본이기 때문
//       Kafka 가 켜져 있으면 → user-service 가 보낸 소식을 post-service 가 받아 writer 를 고친다
//     목록으로 가서 직접 확인해 보자. (소식이 도착하는 데 1초쯤 걸릴 수 있다)

import { useState } from "react";
import { Link } from "react-router";
import { useAuth } from "../context/AuthContext";

function ProfilePage() {
  const { user, changeNickname } = useAuth(); // 로그인한 사람과 닉네임 바꾸기 함수 (AuthContext 가 서버 요청·새 토큰 저장까지 맡는다)
  const [nickname, setNickname] = useState(user.nickname); // ProtectedRoute 안이라 user 는 항상 있다
  const [message, setMessage] = useState(null); // 성공 안내 문구
  const [error, setError] = useState(null); // 실패 이유
  const [busy, setBusy] = useState(false); // 요청 중이면 true → 단추를 막아 두 번 누르기 방지

  const handleSubmit = async (e) => {
    e.preventDefault(); // 페이지 새로 고침 막기
    setBusy(true);
    setError(null); // 지난번 문구는 지우고 시작
    setMessage(null);
    try {
      await changeNickname(nickname.trim()); // PUT /api/auth/me → 게이트웨이 → user-service. 앞뒤 빈칸은 빼고 보낸다
      setMessage("닉네임을 바꿨습니다. 목록에서 예전 글의 작성자도 바뀌었는지 확인해 보세요.");
    } catch (err) {
      setError(err.message); // "닉네임을 입력하세요" 등
    } finally {
      setBusy(false); // 성공이든 실패든 끝나면 단추를 다시 풀어 준다
    }
  };

  return (
    <form className="post-form auth-form" onSubmit={handleSubmit}>
      <h2>내 정보</h2>
      {message && <p className="info-box">{message}</p>}
      {error && <p className="error">⚠️ {error}</p>}
      <label>
        아이디
        {/* 아이디는 바꿀 수 없다 (disabled: 보이기만 하고 입력은 막는다) */}
        <input value={user.username} disabled />
      </label>
      <label>
        닉네임
        <input value={nickname} onChange={(e) => setNickname(e.target.value)} maxLength={30} />
      </label>
      {/* 요청 중이거나, 비었거나, 지금 닉네임과 같으면 단추를 막는다 (보낼 필요가 없으니까) */}
      <button type="submit" className="primary wide" disabled={busy || !nickname.trim() || nickname === user.nickname}>
        {busy ? "바꾸는 중..." : "닉네임 바꾸기"}
      </button>
      <p className="hint">
        {/* ?mine=1 : 목록 화면의 "내 글" 탭으로 바로 간다 → 작성자가 새 닉네임으로 바뀌었는지 확인 */}
        <Link to="/?mine=1">내 글 목록 보기</Link>
      </p>
    </form>
  );
}

export default ProfilePage;
