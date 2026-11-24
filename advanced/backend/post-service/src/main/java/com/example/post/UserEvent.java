package com.example.post;

/**
 * UserEvent - (심화) user-service 가 보내는 회원 소식
 *
 *   { "type": "NICKNAME_CHANGED", "userId": 1, "nickname": "민수킹" }
 *
 * user-service 에도 같은 모양의 UserEvent 가 따로 있다 (코드를 나눠 쓰지 않는다).
 * 두 서비스가 지키는 약속은 이 JSON 의 칸 이름과 뜻이다.
 */
public record UserEvent(String type, Long userId, String nickname) {

	public static final String NICKNAME_CHANGED = "NICKNAME_CHANGED";
}
