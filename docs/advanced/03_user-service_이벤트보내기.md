# 3장. user-service - 닉네임 바꾸기와 이벤트 보내기

## 학습 목표

- `PUT /api/auth/me` 로 닉네임을 바꾸고, **새 토큰**을 돌려주는 이유를 안다.
- `KafkaTemplate` 으로 `user-events` 토픽에 소식(JSON)을 보낸다.
- "DB 저장이 끝난 **다음에** 소식을 보낸다" 는 순서의 의미를 안다.

## 3-1. 라이브러리와 설정

<!-- file: advanced/backend/user-service/build.gradle -->

```groovy
// build.gradle (user-service) - 회원 서비스에 필요한 라이브러리
//
//   webmvc               : REST API 만들기 (@RestController)
//   data-jpa + postgresql : userdb 의 users 테이블 쓰기
//   validation           : 가입 입력 검사 (@NotBlank, @Pattern ...)
//   spring-security-crypto : BCrypt 비밀번호 해시 "도구만" 쓴다.
//                          Spring Security 전체(로그인 필터, 주소 규칙)는 쓰지 않는다.
//                          → 로그인 검사는 api-gateway 가 맡기 때문이다 (MSA 개념: 인증은 정문에서 한 번)
//   jjwt                 : 로그인에 성공하면 JWT 토큰을 "만든다" (검사는 게이트웨이가 한다)
//   springdoc            : http://localhost:8081/docs 에서 API 를 바로 시험해 보기
//   kafka                : (심화) 닉네임이 바뀌면 "바뀌었어요" 소식(이벤트)을 Kafka 로 보낸다

dependencies {
	implementation 'org.springframework.boot:spring-boot-starter-webmvc'
	implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
	implementation 'org.springframework.boot:spring-boot-starter-validation'
	implementation 'org.springframework.security:spring-security-crypto'
	implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:3.2.0'
	implementation 'org.springframework.boot:spring-boot-starter-kafka'      // ← 심화: 이벤트 보내기
	implementation 'io.jsonwebtoken:jjwt-api:0.13.0'
	runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.13.0'
	runtimeOnly 'io.jsonwebtoken:jjwt-jackson:0.13.0'
	runtimeOnly 'org.postgresql:postgresql'
}
```

`spring-boot-starter-kafka` 하나면 Spring Boot 가 Kafka 접속 설정과 `KafkaTemplate`(보내는 도구)을 만들어 준다.

<!-- file: advanced/backend/user-service/src/main/resources/application.yml -->

```yaml
# application.yml - 회원 서비스(user-service) 설정
#   ${이름:기본값} → 환경 변수 "이름" 이 있으면 그 값, 없으면 기본값

server:
  port: 8081                     # 게이트웨이(8080)가 /api/auth/** 요청을 이 포트로 보내 준다

spring:
  servlet:
    encoding:
      force-response: true       # 응답에 "charset=UTF-8" 을 붙인다 → Windows PowerShell 5.1 에서도 한글이 깨지지 않는다
  application:
    name: user-service
  datasource:
    # [MSA 개념] 회원 서비스는 userdb 에만 접속한다. postdb(게시글)는 모른다.
    url: ${DB_URL:jdbc:postgresql://localhost:5436/userdb}
    username: postgres
    password: postgres
  jpa:
    hibernate:
      ddl-auto: update           # User Entity 를 보고 users 테이블을 만든다
    show-sql: true
    open-in-view: false
  kafka:                         # (심화) 이벤트를 보낼 Kafka 주소
    bootstrap-servers: ${KAFKA_SERVERS:localhost:9092}
    producer:
      properties:
        max.block.ms: 3000       # Kafka 가 꺼져 있으면 3초만 기다리고 포기 (기본값 60초는 너무 길다)

# 심화 스위치 - Kafka 로 이벤트를 보낼까?
#   false : 보내지 않는다 (실험용: Kafka 없이 닉네임을 바꾸면 어떻게 되나)
#   true  : 닉네임이 바뀌면 user-events 토픽으로 이벤트를 보낸다 (기본값)
app:
  kafka:
    enabled: ${KAFKA_ENABLED:true}

# JWT(로그인 토큰) 설정 - JwtProvider 가 읽어 간다
jwt:
  # 토큰 서명 열쇠. api-gateway 의 jwt.secret 과 "반드시 같은 값" 이어야 한다.
  #   user-service 가 이 열쇠로 서명 → api-gateway 가 같은 열쇠로 진짜인지 확인
  # 실제 서비스에서는 환경 변수 JWT_SECRET 으로 넣고 GitHub 에 올리지 않는다. (32글자 이상)
  secret: ${JWT_SECRET:dev-only-secret-change-me-0123456789abcdef}
  expiration-minutes: ${ACCESS_TOKEN_MINUTES:60}    # 토큰 유효 시간(분)

springdoc:
  swagger-ui:
    path: /docs                  # http://localhost:8081/docs
```

| 설정 | 뜻 |
|---|---|
| `spring.kafka.bootstrap-servers` | 처음 접속할 Kafka 주소. `localhost:9092` |
| `producer.properties.max.block.ms: 3000` | Kafka 가 꺼져 있을 때 **3초만** 기다리고 포기한다. 기본값(60초)이면 닉네임 바꾸기가 1분 동안 멈춘다 |
| `app.kafka.enabled` | 우리가 만든 스위치. `false` 면 소식을 보내지 않는다 (6장 실험용) |

보내는 값은 **글자(String)** 다. Spring Boot 는 따로 정하지 않으면 키와 값을 글자로 보낸다. 객체를 JSON 글자로 바꾸는 일은 우리 코드(`UserEventPublisher`)가 한다.

## 3-2. 닉네임 바꾸기 - User, NicknameRequest, AuthService

<!-- file: advanced/backend/user-service/src/main/java/com/example/user/NicknameRequest.java -->

```java
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
```

`User` 에는 한 메서드만 더했다.

```java
/** (심화) 닉네임 바꾸기. 트랜잭션이 끝날 때 JPA 가 UPDATE 를 실행한다 (변경 감지) */
public void changeNickname(String nickname) {
    this.nickname = nickname;
}
```

`AuthService` 에 더한 메서드다.

```java
@Transactional
public TokenResponse changeNickname(Long userId, String nickname) {
    User user = userRepository.findById(userId)
            .orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "로그인이 만료되었습니다. 다시 로그인하세요"));
    user.changeNickname(nickname.strip()); // 메서드가 끝나면(커밋) JPA 가 UPDATE users 를 실행한다
    return TokenResponse.bearer(jwtProvider.createToken(user), UserResponse.from(user));
}
```

> **왜 새 토큰을 돌려줄까?**
>
> 기초 4장에서 토큰 안에 **닉네임**을 넣었다. 게이트웨이는 그 닉네임을 `X-User-Nickname` 헤더로 post-service 에 넘기고, post-service 는 그것을 새 글의 `writer` 로 저장한다.
>
> 닉네임을 바꿔도 **이미 발급한 토큰 안의 닉네임은 바뀌지 않는다**(토큰은 서명된 글자라 고칠 수 없다). 옛 토큰을 계속 쓰면 앞으로 쓰는 글이 옛 닉네임으로 저장된다. 그래서 새 닉네임을 담은 토큰을 다시 발급하고, React 가 그것으로 바꿔 끼운다(5장). 옛 토큰으로 쓰면 어떻게 되는지는 6장에서 실험한다.

## 3-3. UserEvent - 소식의 모양

<!-- file: advanced/backend/user-service/src/main/java/com/example/user/UserEvent.java -->

```java
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
```

Kafka 로 나가는 실제 글자는 이렇다.

```json
{"type":"NICKNAME_CHANGED","userId":1,"nickname":"민수킹"}
```

`type` 칸을 둔 이유: 나중에 "회원 탈퇴(USER_DELETED)" 같은 다른 소식도 **같은 토픽**으로 보낼 수 있게 하려는 것이다. 받는 쪽은 `type` 을 보고 무엇을 할지 고른다.

## 3-4. UserEventPublisher - Kafka 로 보내기

<!-- file: advanced/backend/user-service/src/main/java/com/example/user/UserEventPublisher.java -->

```java
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
```

핵심은 한 줄이다.

```java
kafkaTemplate.send("user-events", "1", "{\"type\":\"NICKNAME_CHANGED\",...}");
//                  토픽           키(회원 번호)  값(소식 JSON)
```

- **`send` 는 기다리지 않는다.** 소식을 보낼 준비만 하고 바로 돌아온다. 실제로 Kafka 에 도착했는지는 `whenComplete` 안에서 나중에 알 수 있다. 그래서 닉네임 바꾸기 응답이 Kafka 때문에 느려지지 않는다. (단, 서비스를 켜고 **처음 보낼 때**는 Kafka 와 연결하고 토픽 정보를 받아 오느라 1초쯤 걸릴 수 있다)
- **Kafka 에 아예 닿지 못하면** `send` 가 3초(`max.block.ms`) 기다린 뒤 예외를 던진다. 닉네임은 이미 저장됐으므로 요청을 실패시키지 않고 로그만 남긴다. 이때 **소식은 사라진다**. 이 약점은 6장에서 직접 보고, 7장의 Outbox 패턴으로 해결 방법을 알아본다.

## 3-5. AuthController - 저장 다음에 보낸다

<!-- file: advanced/backend/user-service/src/main/java/com/example/user/AuthController.java -->

```java
package com.example.user;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/**
 * AuthController - 회원가입·로그인·내 정보 API (회원 서비스, 포트 8081)
 *
 *   주소                 방식   로그인   하는 일                       성공
 *   /api/auth/signup     POST   -        회원가입                       201
 *   /api/auth/login      POST   -        로그인 → 토큰 발급              200
 *   /api/auth/me         GET    필요     토큰 주인의 정보                200
 *   /api/auth/me         PUT    필요     (심화) 닉네임 바꾸기 → 새 토큰    200
 *
 * [MSA 개념] "로그인 필요" 검사는 이 서비스가 하지 않는다
 *   React 는 항상 게이트웨이(8080)로 요청한다. 게이트웨이가 토큰을 검사하고,
 *   통과하면 요청 헤더에 "X-User-Id: 3" 을 붙여서 이 서비스로 넘겨 준다.
 *   그래서 이 서비스는 토큰을 볼 필요 없이 @RequestHeader("X-User-Id") 로 번호만 꺼내 쓰면 된다.
 *   (X-User-Id 헤더 없이 8081 로 직접 부르면 GlobalExceptionHandler 가 401 로 응답한다)
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

	private final AuthService authService;
	private final UserEventPublisher eventPublisher;

	public AuthController(AuthService authService, UserEventPublisher eventPublisher) {
		this.authService = authService;
		this.eventPublisher = eventPublisher;
	}

	@PostMapping("/signup")
	@ResponseStatus(HttpStatus.CREATED)
	public UserResponse signup(@Valid @RequestBody SignupRequest request) {
		return authService.signup(request);
	}

	@PostMapping("/login")
	public TokenResponse login(@Valid @RequestBody LoginRequest request) {
		return authService.login(request);
	}

	@GetMapping("/me")
	public UserResponse me(@RequestHeader("X-User-Id") Long userId) { // 게이트웨이가 붙여 준 사용자 번호
		return authService.me(userId);
	}

	/**
	 * (심화) 닉네임 바꾸기  PUT /api/auth/me  { "nickname": "민수킹" }
	 *
	 *   1. authService.changeNickname : userdb 에 저장한다. 메서드가 끝나면 트랜잭션이 커밋된다.
	 *   2. eventPublisher.publish     : 저장이 끝난 "다음에" 소식을 보낸다.
	 *      (순서가 반대면, 저장이 실패했는데 소식만 나가는 일이 생길 수 있다)
	 */
	@PutMapping("/me")
	public TokenResponse changeNickname(@RequestHeader("X-User-Id") Long userId,
			@Valid @RequestBody NicknameRequest request) {
		TokenResponse response = authService.changeNickname(userId, request.nickname()); // 1. 저장 (커밋)
		eventPublisher.publish(UserEvent.nicknameChanged(response.user())); //            2. 소식 보내기
		return response; // 새 토큰 + 바뀐 회원 정보
	}
}
```

`changeNickname` 은 두 줄이다. **순서가 중요하다.**

1. `authService.changeNickname(...)` - `@Transactional` 메서드라서, 이 줄이 끝나면 **DB 저장(커밋)이 끝난 상태**다.
2. `eventPublisher.publish(...)` - 그다음에 소식을 보낸다.

순서를 바꿔 소식을 먼저 보내고 저장에 실패하면? post-service 는 "민수킹으로 바뀌었다" 고 writer 를 고쳤는데, 정작 users 에는 "민수" 가 남는다. **없었던 일을 알린 셈**이다. 그래서 "확실히 일어난 일" 만 알리도록 저장 뒤에 보낸다.

> **[MSA 개념] 이벤트는 "이미 일어난 일"**
>
> 이벤트 이름을 `NICKNAME_CHANGED`(바뀌었다)처럼 **과거형**으로 짓는 것도 같은 뜻이다. "바꿔라(CHANGE_NICKNAME)" 는 명령이고, "바뀌었다" 는 사실이다.

## 3-6. 켜서 시험하기

`UserServiceApplication` 을 ▶ 로 실행하고 http://localhost:8081/docs 를 연다. `PUT /api/auth/me` 가 새로 보인다.

1. `POST /api/auth/signup` 으로 `{"username":"minsu","password":"password123","nickname":"민수"}` 가입
2. `PUT /api/auth/me` → `X-User-Id` 에 `1`, 본문 `{"nickname":"민수킹"}` → **Execute**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": { "id": 1, "username": "minsu", "nickname": "민수킹" }
}
```

IntelliJ 콘솔에 이런 줄이 보이면 소식이 Kafka 에 도착한 것이다.

```text
[이벤트 보냄] user-events → {"type":"NICKNAME_CHANGED","userId":1,"nickname":"민수킹"}
```

**[PS]** Kafka 에 정말 쌓였는지 직접 꺼내 보자 (5초 동안 읽고 끝난다)

```powershell
docker exec mas-adv-kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic user-events --from-beginning --formatter-property print.key=true --timeout-ms 5000
```

```text
1	{"type":"NICKNAME_CHANGED","userId":1,"nickname":"민수킹"}
Processed a total of 1 messages
```

맨 앞의 `1` 이 키(회원 번호)다. 이 명령은 **구경만** 하는 것이라(따로 만든 임시 그룹으로 읽는다) post-service 가 읽을 위치에는 영향을 주지 않는다. (`The consumer rebalance protocol ...` 같은 안내 줄이나 `TimeoutException` 오류 줄이 함께 보일 수 있다. 5초가 지나 읽기를 끝냈다는 뜻이니 괜찮다)

> **post-service 를 아직 켜지 않았는데 소식은 어디에?** Kafka 에 남아 있다. 4장에서 post-service 를 켜면, 켜기 전에 쌓인 이 소식부터 읽어 간다. 이것이 이벤트 방식의 힘이다.

## 정리

- `PUT /api/auth/me` 는 닉네임을 저장하고 **새 토큰**을 돌려준다 (토큰 안 닉네임이 바뀌어야 하므로).
- `KafkaTemplate.send(토픽, 키, 값)` 으로 소식을 보낸다. 키는 회원 번호, 값은 JSON 글자.
- **저장(커밋) 뒤에** 보낸다. 이벤트는 이미 일어난 사실만 알린다.
- Kafka 에 닿지 못하면 3초 뒤 포기하고 로그만 남긴다 → 그 소식은 사라진다 (7장 Outbox).

## 확인 문제

1. 닉네임을 바꾼 뒤 새 토큰을 돌려주지 않으면 어떤 일이 생기는가?
2. 소식을 먼저 보내고 DB 에 저장하면 어떤 문제가 생길 수 있는가?
3. 이벤트 이름을 `CHANGE_NICKNAME` 이 아니라 `NICKNAME_CHANGED` 로 지은 이유는?
4. `max.block.ms` 를 3000 으로 줄인 이유는?
