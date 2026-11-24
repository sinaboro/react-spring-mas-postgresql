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
