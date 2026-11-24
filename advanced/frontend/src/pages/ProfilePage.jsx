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
  const { user, changeNickname } = useAuth();
  const [nickname, setNickname] = useState(user.nickname); // ProtectedRoute 안이라 user 는 항상 있다
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await changeNickname(nickname.trim());
      setMessage("닉네임을 바꿨습니다. 목록에서 예전 글의 작성자도 바뀌었는지 확인해 보세요.");
    } catch (err) {
      setError(err.message); // "닉네임을 입력하세요" 등
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="post-form auth-form" onSubmit={handleSubmit}>
      <h2>내 정보</h2>
      {message && <p className="info-box">{message}</p>}
      {error && <p className="error">⚠️ {error}</p>}
      <label>
        아이디
        <input value={user.username} disabled />
      </label>
      <label>
        닉네임
        <input value={nickname} onChange={(e) => setNickname(e.target.value)} maxLength={30} />
      </label>
      <button type="submit" className="primary wide" disabled={busy || !nickname.trim() || nickname === user.nickname}>
        {busy ? "바꾸는 중..." : "닉네임 바꾸기"}
      </button>
      <p className="hint">
        <Link to="/?mine=1">내 글 목록 보기</Link>
      </p>
    </form>
  );
}

export default ProfilePage;
