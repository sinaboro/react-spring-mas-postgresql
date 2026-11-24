# 부록 A. 오류 해결

기초 과정 부록 A 의 내용(포트 충돌, jwt.secret, PowerShell 한글 등)은 심화 과정에도 그대로 해당한다. 여기에는 심화 과정에서 새로 생길 수 있는 것만 모았다.

## A-1. Kafka

| 증상 | 원인 | 해결 |
|---|---|---|
| `docker compose up -d` 에서 `port is already allocated` (9092) | 다른 Kafka 가 9092 를 쓰고 있다 | 그 Kafka 를 끄거나, compose 의 `"9092:9092"` 와 두 서비스의 `KAFKA_SERVERS`(기본 `localhost:9092`)를 함께 바꾼다 |
| `docker logs mas-adv-kafka` 에 `Kafka Server started` 가 안 보인다 | 아직 켜지는 중이거나 메모리가 부족하다 | 10~20초 기다린다. Docker Desktop 의 메모리 설정을 확인한다 |
| post-service 콘솔에 `Connection to node ... could not be established` 가 계속 찍힌다 | Kafka 가 꺼져 있다 | `docker start mas-adv-kafka`. 켜지면 저절로 다시 붙는다 |
| 켜자마자 `NotCoordinatorException` INFO 줄 | Kafka 가 그룹 정보를 저장할 곳을 처음 만드는 중 | 무시해도 된다. `partitions assigned` 가 나오면 정상 |

## A-2. 이벤트가 오지 않는다

| 증상 | 원인 | 해결 |
|---|---|---|
| 닉네임을 바꿔도 예전 글 작성자가 그대로, user-service 콘솔에 `[이벤트 꺼짐]` | user-service 의 `app.kafka.enabled` 가 `false` | `application.yml` 에서 `true` 로 바꾸고 다시 켠다 |
| user-service 는 `[이벤트 보냄]` 인데 post-service 에 `[이벤트 받음]` 이 없다 | post-service 의 `app.kafka.enabled` 가 `false` 라 듣지 않는다 | post-service 의 `application.yml` 도 `true` 로 |
| 닉네임 바꾸기가 3초쯤 걸리고 `[이벤트 실패] Kafka 에 연결할 수 없습니다` | 보내는 순간 Kafka 가 꺼져 있었다 | Kafka 를 켜고 닉네임을 다시 바꾼다. 그 소식은 사라졌다 (6장 실험 ④, 7장 Outbox) |
| 목록에 옛 닉네임이 잠깐 보인다 | 소식이 도착하기 전(1초 남짓) | 잠시 뒤 다시 연다 (결과적 일관성) |
| 새로 쓴 글만 옛 닉네임이다 | 닉네임을 바꾸기 전에 받은 **옛 토큰**으로 썼다 | 다시 로그인하거나, 내 정보 화면에서 바꿔 새 토큰을 받는다 (6장 실험 ③) |

## A-3. 기타

| 증상 | 원인 | 해결 |
|---|---|---|
| 서비스 콘솔에 `Connection to localhost:5436 refused` | 심화 DB(`mas-adv-db`)가 꺼져 있다 / 기초 DB(5435)만 켰다 | `advanced` 폴더에서 `docker compose up -d` |
| 회원가입이 `이미 사용 중인 아이디입니다` | 3장이나 6장에서 이미 만들었다 | 로그인한다 |
| DB 를 지웠는데(`down -v`) 예전 닉네임 소식이 또 처리된다 | Kafka 에는 예전 소식이 남아 있다 (컨테이너를 지우지 않았으므로) | 문제는 없다(멱등). 깨끗이 하려면 `docker compose down -v` 로 Kafka 컨테이너까지 지운다 |
| `kafka-console-consumer.sh` 뒤에 `TimeoutException` 오류 줄 | `--timeout-ms 5000` 이 지나 읽기를 끝냈다는 뜻 | 무시해도 된다 |
