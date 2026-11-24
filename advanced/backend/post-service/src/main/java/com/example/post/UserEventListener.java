package com.example.post;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.databind.json.JsonMapper;

/**
 * UserEventListener - (심화) Kafka 의 user-events 토픽을 "듣는" 곳
 *
 * [MSA 개념] 복사본은 소식을 듣고 스스로 맞춘다
 *   posts.writer 는 닉네임의 복사본이다(5장). 원본(userdb.users.nickname)이 바뀌면
 *   user-service 가 "NICKNAME_CHANGED" 소식을 올리고, 이 클래스가 그 소식을 받아 writer 를 고친다.
 *   user-service 는 post-service 를 부르지 않았고, post-service 도 userdb 를 보지 않았다.
 *
 *   @KafkaListener
 *     topics      : 들을 토픽
 *     autoStartup : app.kafka.enabled 가 true 일 때만 듣기 시작한다 (기본값 true)
 *     group-id    : application.yml 의 post-service. Kafka 는 이 이름으로 "어디까지 읽었는지" 를 기억한다.
 *                   그래서 post-service 가 꺼져 있던 동안 쌓인 소식도, 다시 켜지면 이어서 읽는다.
 *
 * 같은 소식을 두 번 받아도 괜찮다: "writer 를 민수킹으로" 는 몇 번 해도 결과가 같다 (멱등성).
 */
@Component
public class UserEventListener {

	private static final Logger log = LoggerFactory.getLogger(UserEventListener.class);

	private final PostRepository postRepository;
	private final JsonMapper jsonMapper; // JSON 글자 → UserEvent 객체

	public UserEventListener(PostRepository postRepository, JsonMapper jsonMapper) {
		this.postRepository = postRepository;
		this.jsonMapper = jsonMapper;
	}

	@KafkaListener(topics = "user-events", autoStartup = "${app.kafka.enabled}")
	@Transactional // UPDATE 쿼리(@Modifying)는 트랜잭션 안에서 실행해야 한다
	public void onUserEvent(String message) {
		UserEvent event = jsonMapper.readValue(message, UserEvent.class);
		if (UserEvent.NICKNAME_CHANGED.equals(event.type())) {
			int count = postRepository.updateWriter(event.userId(), event.nickname());
			log.info("[이벤트 받음] {}번 회원 닉네임 → {} (글 {}개 고침)", event.userId(), event.nickname(), count);
		} else {
			log.info("[이벤트 받음] 모르는 종류라 넘어감: {}", message); // 나중에 생길 소식 종류는 무시
		}
	}
}
