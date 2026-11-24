package com.example.user;

/**
 * UserEvent - (심화) 다른 서비스에 알리는 "회원 소식(이벤트)"
 *
 * Kafka 의 user-events 토픽에 아래 JSON 글자로 실려 간다.
 *   { "type": "NICKNAME_CHANGED", "userId": 1, "nickname": "민수킹" }
 *
 * [MSA 개념] 서비스끼리 코드는 나눠 쓰지 않는다
 *   post-service 에도 똑같은 모양의 UserEvent 가 "따로" 있다. 이 클래스를 import 하지 않는다.
 *   두 서비스가 지키는 약속은 클래스가 아니라 "JSON 모양" 이다.
 *   (그래서 칸 이름을 바꿀 때는 받는 쪽과 함께 바꿔야 한다)
 */
public record UserEvent(String type, Long userId, String nickname) {

	public static final String NICKNAME_CHANGED = "NICKNAME_CHANGED";

	public static UserEvent nicknameChanged(UserResponse user) {
		return new UserEvent(NICKNAME_CHANGED, user.id(), user.nickname());
	}
}
