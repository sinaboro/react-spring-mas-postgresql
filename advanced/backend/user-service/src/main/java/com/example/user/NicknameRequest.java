package com.example.user;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * NicknameRequest - (심화) 닉네임 바꾸기 요청 JSON  { "nickname": "민수킹" }
 * 규칙은 회원가입(SignupRequest)의 닉네임 규칙과 같다.
 */
public record NicknameRequest(
		@NotBlank(message = "닉네임을 입력하세요")
		@Size(max = 30, message = "닉네임은 30자까지 쓸 수 있습니다")
		String nickname
) {
}
