package com.example.user;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;
import tools.jackson.databind.json.JsonMapper;

/**
 * UserEventPublisher - (심화) 회원 소식을 Kafka 로 "보내는" 곳
 *
 * [MSA 개념] 이벤트 = "이런 일이 있었어요" 라는 소식
 *   user-service 는 post-service 를 직접 부르지 않는다. 누가 들을지도 모른다.
 *   그저 Kafka 의 user-events 토픽(게시판 같은 곳)에 소식을 올려 둘 뿐이다.
 *   듣고 싶은 서비스(post-service, 나중에 생길 comment-service ...)가 각자 가져가 읽는다.
 *   → 보내는 쪽과 받는 쪽이 서로를 몰라도 된다 (느슨한 연결)
 *
 *   KafkaTemplate.send(토픽, 키, 값)
 *     토픽 : user-events
 *     키   : 회원 번호 "1" - 같은 키의 소식은 같은 칸(파티션)에 들어가 보낸 순서대로 읽힌다
 *     값   : 소식 JSON 글자
 *
 * app.kafka.enabled 가 false 면 보내지 않고 로그만 남긴다.
 */
@Component
public class UserEventPublisher {

	private static final Logger log = LoggerFactory.getLogger(UserEventPublisher.class);
	private static final String TOPIC = "user-events";

	private final KafkaTemplate<String, String> kafkaTemplate;
	private final JsonMapper jsonMapper; // 객체 ↔ JSON 글자 바꾸기 (Spring Boot 가 만들어 둔 것)
	private final boolean enabled;

	public UserEventPublisher(KafkaTemplate<String, String> kafkaTemplate, JsonMapper jsonMapper,
			@Value("${app.kafka.enabled}") boolean enabled) {
		this.kafkaTemplate = kafkaTemplate;
		this.jsonMapper = jsonMapper;
		this.enabled = enabled;
	}

	public void publish(UserEvent event) {
		if (!enabled) {
			log.info("[이벤트 꺼짐] app.kafka.enabled=false 라서 보내지 않음: {}", event);
			return;
		}
		String json = jsonMapper.writeValueAsString(event); // UserEvent → {"type":...} 글자
		try {
			kafkaTemplate.send(TOPIC, String.valueOf(event.userId()), json)
					// send 는 기다리지 않고 바로 돌아온다. 결과는 나중에 이 안에서 알 수 있다
					.whenComplete((result, ex) -> {
						if (ex == null) {
							log.info("[이벤트 보냄] {} → {}", TOPIC, json);
						} else {
							log.warn("[이벤트 실패] Kafka 가 켜져 있나요? {}", ex.getMessage());
						}
					});
		} catch (Exception e) {
			// Kafka 에 아예 닿지 못하면 send 가 3초(max.block.ms) 기다린 뒤 바로 예외를 던진다.
			// 닉네임은 이미 userdb 에 저장됐으므로 요청은 실패시키지 않고 로그만 남긴다.
			// → 이 소식은 사라진다! posts.writer 는 옛 닉네임으로 남는다 (교안의 "Outbox 패턴" 참고)
			log.warn("[이벤트 실패] Kafka 에 연결할 수 없습니다: {}", e.getMessage());
		}
	}
}
