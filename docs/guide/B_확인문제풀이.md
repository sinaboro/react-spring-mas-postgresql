# 부록 B. 확인 문제 풀이

## 1장

1. 모놀리식에서는 회원 기능까지 들어 있는 **서버 전체**를 다시 빌드·배포한다. MSA 에서는 **post-service 만** 다시 배포하면 된다.
2. React 는 게이트웨이(8080) 하나로만 요청하고, 게이트웨이가 주소를 보고 알맞은 서비스로 전달(라우팅)하기 때문이다.
3. 토큰 검사는 게이트웨이가 끝내고, post-service 에는 검사 결과(`X-User-Id`, `X-User-Nickname`)만 헤더로 오기 때문이다.
4. 글을 쓸 때 작성자 번호와 닉네임을 `posts` 테이블에 **복사해서**(`user_id`, `writer`) 저장해 두고, 목록에서는 그 값을 그대로 보여 준다.

## 2장

1. 할 수 없다. PostgreSQL 은 서로 다른 데이터베이스의 테이블을 한 SQL 로 JOIN 하지 못한다(외래 키도 마찬가지).
2. `init.sql` 은 데이터 볼륨이 비어 있을 때 **처음 한 번만** 실행된다. 이미 볼륨이 있으니 다시 실행되지 않았다. `docker compose down -v` 로 볼륨을 지우고 다시 켜거나, `docker exec mas-db psql -U postgres -c "CREATE DATABASE commentdb"` 로 직접 만든다.
3. `user-service/src/main/resources/application.yml` 의 `spring.datasource.url` (또는 환경 변수 `DB_URL`) 하나다.

## 3장

1. post-service 는 토큰을 만들지도 검사하지도 않는다. 검사는 게이트웨이가 하고 결과만 헤더로 받기 때문이다.
2. `backend` 폴더에서 `.\gradlew.bat :post-service:bootRun`
3. `include 'comment-service'`

## 4장

1. 로그인 검사(필터, 주소 규칙)는 게이트웨이가 맡으므로 Spring Security 전체가 필요 없다. 비밀번호 해시 도구(BCrypt)만 있으면 된다.
2. 토큰 내용은 서명만 되어 있을 뿐 암호화되지 않아서 **누구나 읽을 수 있다**. 해시라도 노출되면 비밀번호를 알아내려는 공격에 쓰일 수 있다.
3. 401 `{"detail": "로그인이 필요합니다"}`. `@RequestHeader("X-User-Id")` 가 없어서 생긴 `MissingRequestHeaderException` 을 `GlobalExceptionHandler.handleMissingHeader` 가 401 로 바꾼다.

## 5장

1. 닉네임이 `posts.writer` 에 들어 있어서 users 와 JOIN 할 필요가 없기 때문이다. (애초에 다른 DB 라서 JOIN 할 수도 없다)
2. 버그라기보다 **데이터 복제의 대가**다. 해결하려면 user-service 가 닉네임이 바뀌었다는 소식(이벤트)을 보내고, post-service 가 그 사람 글의 `writer` 를 고친다. 또는 글 목록을 보여 줄 때 user-service 에 닉네임을 물어볼 수도 있다(대신 서비스끼리 묶인다).
3. "이 글의 주인이 누구인가" 는 postdb 에만 있는 정보이기 때문이다. 데이터를 가진 서비스가 그 데이터에 대한 규칙을 지킨다.
4. `writer` 다. `id → user_id → writer` 의 이행 종속이 생겨 **제3정규형(3NF)** 을 어긴다. `user_id` 는 회원을 가리키기만 하므로 위반이 아니다(잃은 것은 FK 의 참조 무결성). 그런데도 이렇게 하는 이유는, DB 를 나눠 JOIN 을 쓸 수 없는 상황에서 글을 읽을 때마다 user-service 를 부르지 않고 **서비스끼리 독립**하기 위해서다. (`writer` 를 "글을 쓸 당시의 닉네임" 으로 정의하면 글에 속한 기록이 되어 위반으로 보지 않을 수도 있다)

## 6장

1. 누구나 `X-User-Id: 1` 을 적어 보내 1번 회원 행세를 할 수 있다. 남의 글 수정·삭제, 남의 이름으로 글쓰기가 가능해진다.
2. 게이트웨이 `application.yml` 의 post-service `uri` 를 `http://localhost:9000` 으로 (그리고 post-service 의 `server.port` 를 9000 으로). React 는 고칠 것이 없다.
3. 게이트웨이가 토큰 서명을 확인하지 못하므로 401 `로그인이 만료되었습니다. 다시 로그인하세요` 가 온다. (로그인 자체는 user-service 가 하므로 성공한다)
4. 브라우저가 보는 서버는 게이트웨이 하나이기 때문이다. 서비스에도 CORS 를 켜면 응답에 CORS 헤더가 겹쳐 붙어 브라우저가 거부할 수 있다.

## 7장

1. 토큰 검사는 게이트웨이가 (같은 비밀 열쇠로) 하고, 글 저장은 post-service 가 하므로 user-service 가 필요 없다. 닉네임도 토큰 안에 들어 있다. 단, 브라우저를 새로고침하면 React 가 `/api/auth/me`(user-service)로 토큰을 확인하다 실패해 로그아웃된다.
2. 로그인은 **된다**(user-service 와 userdb 만 쓴다). 글 목록 · 글쓰기는 게이트웨이가 503 `서비스에 연결할 수 없습니다` 를 돌려준다. React 머리글의 "민수 님"(`/api/auth/me`)도 user-service 가 하므로 잘 나온다.
3. 모든 요청이 멈춘다(React 에는 `API 서버에 연결할 수 없습니다`). 실제 운영에서는 게이트웨이를 **여러 대** 띄우고 그 앞에 로드 밸런서를 두어, 한 대가 죽어도 다른 게이트웨이가 요청을 받게 한다.
