# 4장. post-service - 이벤트 받아 writer 고치기

## 학습 목표

- `@KafkaListener` 로 `user-events` 토픽을 듣는다.
- 받은 소식(JSON)을 객체로 바꿔, 그 회원 글의 `writer` 를 한꺼번에 고친다.
- **컨슈머 그룹**과 `auto-offset-reset`, **멱등성**의 뜻을 코드에서 확인한다.

## 4-1. 설정

<!-- file: advanced/backend/post-service/src/main/resources/application.yml -->

```yaml
# application.yml - 게시글 서비스(post-service) 설정
#   ${이름:기본값} → 환경 변수 "이름" 이 있으면 그 값, 없으면 기본값

server:
  port: 8082                     # 게이트웨이(8080)가 /api/posts/** 요청을 이 포트로 보내 준다

spring:
  servlet:
    encoding:
      force-response: true       # 응답에 "charset=UTF-8" 을 붙인다 → Windows PowerShell 5.1 에서도 한글이 깨지지 않는다
  application:
    name: post-service
  datasource:
    # [MSA 개념] 게시글 서비스는 postdb 에만 접속한다. userdb(회원)는 모른다.
    #   그래서 posts.user_id 에서 users 로 외래 키(FK)를 걸 수 없고, JOIN 도 할 수 없다.
    url: ${DB_URL:jdbc:postgresql://localhost:5436/postdb}
    username: postgres
    password: postgres
  jpa:
    hibernate:
      ddl-auto: update           # Post Entity 를 보고 posts 테이블을 만든다
    show-sql: true
    open-in-view: false
  kafka:                         # (심화) 이벤트를 받을 Kafka 주소
    bootstrap-servers: ${KAFKA_SERVERS:localhost:9092}
    consumer:
      group-id: post-service     # "나는 post-service 다" - Kafka 가 어디까지 읽었는지 이 이름으로 기억한다
      auto-offset-reset: earliest  # 처음 붙을 때는 토픽의 맨 처음 이벤트부터 읽는다 (놓친 이벤트가 없게)

# JWT 설정이 없다 - 게시글 서비스는 토큰을 다루지 않는다 (게이트웨이가 검사한다)

# 심화 스위치 - Kafka 에서 이벤트를 받을까?
#   false : 받지 않는다 (실험용)
#   true  : user-events 토픽을 듣고, 닉네임이 바뀌면 그 사람 글의 writer 를 고친다 (기본값)
app:
  kafka:
    enabled: ${KAFKA_ENABLED:true}

springdoc:
  swagger-ui:
    path: /docs                  # http://localhost:8082/docs
```

| 설정 | 뜻 |
|---|---|
| `consumer.group-id: post-service` | 이 서비스의 **컨슈머 그룹** 이름. Kafka 는 이 이름으로 "어디까지 읽었는지(오프셋)" 를 기억한다 |
| `consumer.auto-offset-reset: earliest` | 이 그룹이 **처음** 토픽에 붙을 때 맨 처음 소식부터 읽는다. 기본값 `latest` 면 "붙은 뒤에 온 소식" 만 읽어서, 3장에서 미리 보낸 소식을 놓친다 |

`auto-offset-reset` 은 "기억해 둔 위치가 **없을 때만**" 쓰인다. 한 번 읽기 시작한 뒤에는 Kafka 가 기억해 둔 위치 다음부터 읽는다.

## 4-2. writer 를 바꿀 수 있게 - Post, PostRepository

기초 과정의 `Post.writer` 에는 `updatable = false`(처음 저장한 뒤 바꾸지 않음)가 붙어 있었다. 이제는 닉네임 변경 소식을 받으면 바뀌어야 하므로 뺐다.

```java
@Column(nullable = false, length = 30)
private String writer; // 글쓴이 닉네임 (복사본. 닉네임 변경 이벤트를 받으면 바뀐다)
```

<!-- file: advanced/backend/post-service/src/main/java/com/example/post/PostRepository.java -->

```java
package com.example.post;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

/**
 * PostRepository - posts 테이블 창구
 *
 *   findAllByOrderByIdDesc()           전체 글, 최근 글이 위로        → ORDER BY id DESC
 *   findAllByUserIdOrderByIdDesc(3)    3번 회원의 글만 ("내 글" 보기) → WHERE user_id = 3
 *   findById(5)                        글 하나 (JpaRepository 기본 기능)
 *   updateWriter(3, "민수킹")           (심화) 3번 회원 글의 writer 를 한 번에 바꾸기
 *
 * 모놀리식 판에 있던 @EntityGraph(작성자 JOIN)가 없다.
 * 닉네임이 posts 테이블 안(writer)에 있으니 JOIN 할 필요가 없다 → 쿼리가 오히려 단순해졌다.
 */
public interface PostRepository extends JpaRepository<Post, Long> {

	List<Post> findAllByOrderByIdDesc();

	List<Post> findAllByUserIdOrderByIdDesc(Long userId);

	/**
	 * (심화) UPDATE posts SET writer = '민수킹' WHERE user_id = 3
	 *   @Query    : 메서드 이름 대신 직접 쓴 JPQL 을 실행한다 (Post, userId 는 Entity·필드 이름)
	 *   @Modifying: SELECT 가 아니라 바꾸는 쿼리라는 표시. 돌려주는 int 는 바뀐 줄 수
	 */
	@Modifying
	@Query("update Post p set p.writer = :writer where p.userId = :userId")
	int updateWriter(@Param("userId") Long userId, @Param("writer") String writer);
}
```

`updateWriter` 는 글을 하나씩 읽어 고치지 않고, **UPDATE 한 번**으로 그 회원의 글을 모두 고친다. 글이 100개여도 SQL 은 하나다.

```sql
update posts set writer = '민수킹' where user_id = 1
```

## 4-3. UserEvent - 같은 모양, 다른 클래스

<!-- file: advanced/backend/post-service/src/main/java/com/example/post/UserEvent.java -->

```java
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
```

user-service 의 `UserEvent` 와 칸이 같지만 **다른 클래스**다. post-service 는 user-service 의 코드를 가져다 쓰지 않는다.

> **[MSA 개념] 약속은 코드가 아니라 메시지 모양**
>
> 두 서비스가 `UserEvent` 클래스를 함께 쓰는 공통 라이브러리를 만들면 편해 보인다. 하지만 그러면 한쪽이 그 라이브러리를 바꿀 때 다른 쪽도 같이 다시 배포해야 한다. 서비스를 따로 배포하려고 나눴는데 다시 묶이는 것이다. 그래서 "JSON 칸 이름과 뜻" 만 약속하고, 클래스는 각자 둔다. 칸을 바꿀 때는 **받는 쪽이 먼저** 새 칸을 알아듣게 고친 뒤 보내는 쪽을 바꾼다.

## 4-4. UserEventListener - 소식 듣기

<!-- file: advanced/backend/post-service/src/main/java/com/example/post/UserEventListener.java -->

```java
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
```

- `@KafkaListener(topics = "user-events")` - Spring 이 Kafka 에 붙어 이 토픽을 계속 지켜보다가, 소식이 오면 `onUserEvent(String message)` 를 불러 준다. `message` 는 3장에서 보낸 JSON 글자 그대로다.
- `jsonMapper.readValue(message, UserEvent.class)` - JSON 글자 → `UserEvent` 객체.
- `type` 이 `NICKNAME_CHANGED` 이면 `updateWriter` 를 실행한다. 모르는 종류는 로그만 남기고 넘어간다. 나중에 user-service 가 새 종류의 소식을 보내도 post-service 가 망가지지 않는다.
- `@Transactional` - UPDATE 쿼리(`@Modifying`)는 트랜잭션 안에서 실행해야 한다.

**메서드가 오류 없이 끝나면** Spring 이 Kafka 에 "여기까지 읽었다(오프셋)" 고 알린다. 처리 중에 오류가 나면 같은 소식을 다시 받는다. (Spring 기본 설정은 몇 번 다시 시도해 보고, 그래도 안 되면 오류 로그를 남기고 다음 소식으로 넘어간다)

> **[MSA 개념] 멱등성 - 같은 소식을 두 번 받아도 괜찮게**
>
> Kafka 는 "소식을 **적어도 한 번**은 전달한다" 를 약속한다. 처리는 끝났는데 "다 읽었다" 를 알리기 직전에 서비스가 죽으면, 다시 켜졌을 때 같은 소식을 **한 번 더** 받는다.
>
> "writer 를 민수킹으로 바꿔라" 는 두 번 해도 결과가 같다. 이렇게 **여러 번 해도 결과가 같은 성질**을 **멱등성(idempotency)** 이라고 한다. 반대로 "포인트 100 더하기" 같은 소식은 두 번 받으면 200 이 더해진다. 그런 소식은 "이미 처리한 소식 번호" 를 따로 기록해 두는 등 더 조심해야 한다.

## 4-5. 켜서 시험하기

`PostServiceApplication` 을 ▶ 로 실행한다. 콘솔에서 두 가지를 확인한다.

```text
post-service: partitions assigned: [user-events-0]
[이벤트 받음] 1번 회원 닉네임 → 민수킹 (글 0개 고침)
```

1. **partitions assigned** - post-service 가 `user-events` 토픽의 0번 칸을 맡았다(구독 성공).
2. **이벤트 받음** - 3장에서 post-service 가 꺼져 있을 때 보낸 소식을 **지금** 받았다(`earliest` 덕분). 아직 글이 없어서 0개를 고쳤다.

> 켜자마자 `NotCoordinatorException` 같은 INFO 줄이 몇 번 보일 수 있다. Kafka 가 처음으로 "그룹별 읽은 위치" 를 저장할 곳을 만드는 중이라는 뜻이고, 1~2초 뒤 `partitions assigned` 가 나오면 정상이다.

**[PS]** Kafka 가 기억하는 post-service 그룹의 읽은 위치

```powershell
# post-service 그룹이 어디까지 읽었는지 보기: CURRENT-OFFSET(읽은 위치), LOG-END-OFFSET(마지막 위치), LAG(밀린 개수)
docker exec mas-adv-kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group post-service
```

```text
GROUP         TOPIC        PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG  (오른쪽 CONSUMER-ID 등은 생략)
post-service  user-events  0          1               1               0
```

숫자는 3장에서 닉네임을 몇 번 바꿨는지에 따라 다르다. 중요한 것은 `LAG` 이 0 인지다.

| 칸 | 뜻 |
|---|---|
| `CURRENT-OFFSET` | post-service 가 다음에 읽을 위치 (= 지금까지 읽은 개수) |
| `LOG-END-OFFSET` | 토픽에 쌓인 소식 개수 |
| `LAG` | 아직 못 읽은 소식 개수 (둘의 차이). 0 이면 다 따라잡았다 |

6장에서 post-service 를 끈 채 닉네임을 바꾸면 `LAG` 이 늘어나는 것을 본다.

## 정리

- `@KafkaListener` 가 토픽을 지켜보다가 소식이 오면 메서드를 불러 준다.
- 소식을 받으면 `UPDATE posts SET writer = ? WHERE user_id = ?` 한 번으로 그 회원 글을 고친다.
- 컨슈머 그룹마다 읽은 위치를 Kafka 가 기억한다. 처음 붙을 때는 `earliest` 로 맨 앞부터 읽는다.
- 같은 소식을 두 번 받을 수 있으므로 처리는 **멱등**하게 만든다.

## 확인 문제

1. `auto-offset-reset` 을 `latest` 로 두면 3장에서 미리 보낸 소식은 어떻게 되는가?
2. post-service 가 user-service 의 `UserEvent` 클래스를 가져다 쓰지 않는 이유는?
3. "writer 를 민수킹으로" 는 멱등한데 "글 수 1 더하기" 는 멱등하지 않다. 왜 그런가?
4. `kafka-consumer-groups.sh` 결과의 `LAG` 이 3 이라면 무슨 뜻인가?
