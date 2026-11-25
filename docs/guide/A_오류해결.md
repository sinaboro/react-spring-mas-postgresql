# 부록 A. 오류 해결

## A-0. 준비 · 폴더

| 증상 | 원인 | 해결 |
|---|---|---|
| `docker`, `git`, `node`, `npm` 이 "인식되지 않습니다" | 설치하지 않았거나, 설치 전에 연 PowerShell 창이다 | 설치한 뒤 PowerShell 창을 **새로** 연다. Docker 는 Docker Desktop 을 실행해 둔다 |
| `docker compose up` 에서 `failed to connect to the docker API` | Docker Desktop 이 꺼져 있다 | Docker Desktop 을 실행하고 고래 아이콘이 멈출 때까지 기다린다 |
| `no configuration file provided: not found` | `docker-compose.yml` 이 없는 폴더에서 쳤다 | `cd C:\study\react-spring-mas-postgresql` 후 다시 |
| `.\gradlew.bat` 이 "인식되지 않습니다" | `backend` 폴더가 아닌 곳에서 쳤다 | `cd C:\study\react-spring-mas-postgresql\backend` 후 다시 |
| `npm run dev` 가 `Could not read package.json` | `frontend` 폴더가 아닌 곳에서 쳤다 | `cd C:\study\react-spring-mas-postgresql\frontend` 후 다시 |
| 붙여 넣은 명령이 `>>` 를 보이며 멈춘다 | 따옴표나 `{ }` 가 덜 닫힌 채 붙여 넣어졌다 | Ctrl+C 로 멈추고 상자 전체를 다시 복사해 붙여 넣는다 |

## A-1. DB

| 증상 | 원인 | 해결 |
|---|---|---|
| 서비스 콘솔에 `database "userdb" does not exist` | 예전 볼륨이 남아 있어 `init.sql` 이 실행되지 않았다 | 저장소 폴더에서 `docker compose down -v` → `docker compose up -d` (데이터가 지워진다) |
| `Connection to localhost:5435 refused` | DB 컨테이너가 꺼져 있다 | `docker compose up -d`, `docker compose ps` 로 healthy 확인 |
| `port is already allocated` (5435) | 다른 프로그램이 5435 를 쓰고 있다 | `docker-compose.yml` 의 `"5435:5432"` 를 `"5437:5432"` 처럼 비어 있는 포트로 바꾸고, 두 서비스의 `DB_URL` 기본값 포트도 같이 바꾼다 (5436 은 MSA 심화 과정 DB 가 쓰므로 피한다) |

## A-2. 서비스 실행

| 증상 | 원인 | 해결 |
|---|---|---|
| `Port 8080 was already in use` | 다른 서버(예: React 심화 과정 게시판)가 8080 을 쓰고 있다 | 그 서버를 끄거나, IntelliJ Services 창에서 중복 실행된 것을 멈춘다 |
| `Port 8081 (8082) was already in use` | 같은 서비스를 두 번 켰다 | Services 창(`Alt + 8`)에서 하나를 멈춘다 |
| Gradle sync 가 실패한다 | JDK 21 이 아니다 / 인터넷 연결 | **File → Project Structure → SDK** 를 21 로, Gradle 창의 🔄 로 다시 sync |
| 게이트웨이 콘솔에 `HV000271 ... deprecated` 경고 | 라이브러리 안쪽 경고 | 무시해도 된다. `Started GatewayApplication` 이 보이면 정상 |

## A-3. 요청과 응답

| 증상 | 원인 | 해결 |
|---|---|---|
| 로그인 뒤 글쓰기가 계속 `로그인이 만료되었습니다` (401) | 게이트웨이와 user-service 의 `jwt.secret` 이 다르다 | 두 `application.yml` 의 `jwt.secret` 을 같은 값으로 |
| 로그인 · 회원가입이 `서비스에 연결할 수 없습니다` (503) | user-service 가 꺼져 있다 | `UserServiceApplication` ▶ |
| 글 목록이 `서비스에 연결할 수 없습니다` (503) | post-service 가 꺼져 있다 | `PostServiceApplication` ▶ |
| React 에서 `API 서버에 연결할 수 없습니다` | 게이트웨이(8080)가 꺼져 있다 | `GatewayApplication` ▶ |
| 브라우저 콘솔에 CORS 오류 | React 가 8081 · 8082 로 직접 요청하고 있다 / 서비스에도 CORS 를 켰다 | `API_URL` 을 8080 으로. CORS 는 게이트웨이에서만 |
| 서비스를 직접(8082) 불렀더니 `로그인이 필요합니다` (401) | `X-User-Id` 헤더가 없다 | 게이트웨이(8080)로 부르거나, `/docs` 에서 헤더 칸을 채운다 |
| PowerShell 에서 한글이 `íì¤í¸` 처럼 깨진다 | 응답에 charset 이 없다 / 요청에 charset 이 없다 | 서비스 `application.yml` 에 `spring.servlet.encoding.force-response: true`, 요청은 `-ContentType "application/json; charset=utf-8"` |
| user-service 를 끈 뒤 새로고침(F5)했더니 로그아웃됐다 | React 가 새로 열릴 때 `/api/auth/me`(user-service)로 토큰을 확인하는데, 503 이 와서 토큰을 지웠다 | 정상 동작이다(7-5). user-service 를 켜고 다시 로그인한다. 고쳐 보려면 8장 도전 과제 4 |
| 7장 회원가입에서 `이미 사용 중인 아이디입니다` (409) | 4장에서 minsu 를 이미 만들었다 | 가입하지 말고 로그인한다 |
| `/docs` 에서 `GET /api/auth/me` 를 Execute 해도 요청이 가지 않고 칸이 빨개진다 | `X-User-Id` 칸이 필수인데 비어 있다 | 칸에 `1` 을 넣는다. 헤더 없이 보내 보려면 4-8 의 PowerShell 명령 |
| `/docs` 에서 `X-User-Nickname` 에 한글을 넣으니 오류가 난다 | 헤더에는 한글을 바로 실을 수 없다 | 영문으로 넣거나 `%EB%AF%BC%EC%88%98` 처럼 인코딩한 값을 넣는다 |
| 글쓴이 닉네임이 `%EB%AF%BC...` 로 저장됐다 | post-service 에서 URL 디코딩을 빠뜨렸다 | `PostController.create` 의 `URLDecoder.decode(...)` 확인 |
