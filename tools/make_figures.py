"""교안에 들어가는 MSA 개념 그림을 만든다 (docs/images/fig_*.png).

    python tools/make_figures.py

matplotlib 으로 상자와 화살표를 그린다. 글꼴은 맑은 고딕(Windows 기본).
화면 캡처(s*_*.png)는 이 파일이 아니라 실제 앱을 실행해 찍은 것이다.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

OUT = Path(__file__).resolve().parent.parent / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, CYAN, GREEN, ORANGE, RED, GREY = "#1f3a5f", "#03588C", "#61dafb", "#2e7d32", "#e8890c", "#c0392b", "#6b7280"
FILL = {"navy": "#e3ebf5", "cyan": "#e0f7fd", "green": "#e6f4ea", "orange": "#fff1dc", "red": "#fdecea",
        "grey": "#f1f3f5", "white": "#ffffff", "teal": "#e0f5f3"}
EDGE = {"navy": NAVY, "cyan": "#1aa3c8", "green": GREEN, "orange": ORANGE, "red": RED, "grey": GREY,
        "white": GREY, "teal": "#1f9e93"}


def canvas(w, h):
    """가로 w, 세로 h 인치 그림. 좌표는 (0~w*10, 0~h*10)"""
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, w * 10)
    ax.set_ylim(0, h * 10)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, color="navy", size=10, bold=False, align="center", dashed=False, va="center"):
    """(x, y) 는 왼쪽 아래. text 는 여러 줄 가능."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                                fc=FILL[color], ec=EDGE[color], lw=1.4, clip_on=False,
                                linestyle="--" if dashed else "-"))
    tx = x + w / 2 if align == "center" else x + 1.2
    ty = y + h / 2 if va == "center" else y + h - 1.2
    ax.text(tx, ty, text, ha=align, va=va, fontsize=size,
            fontweight="bold" if bold else "normal", color="#1f2937", linespacing=1.5)


def arrow(ax, x1, y1, x2, y2, label="", color=NAVY, both=False, rad=0.0, size=8.5, lx=0, ly=0, dashed=False):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="<|-|>" if both else "-|>",
                                 mutation_scale=13, color=color, lw=1.5,
                                 connectionstyle=f"arc3,rad={rad}", linestyle="--" if dashed else "-", clip_on=False))
    if label:
        ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, ha="center", va="center", fontsize=size,
                color=color, bbox=dict(fc="white", ec="none", pad=1.5), linespacing=1.4)


def note(ax, x, y, text, color=GREY, size=8.5, ha="center", bold=False):
    ax.text(x, y, text, ha=ha, va="center", fontsize=size, color=color, linespacing=1.45,
            fontweight="bold" if bold else "normal")


def title(ax, text, x=None, y=None):
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.text(x if x is not None else xl[1] / 2, y if y is not None else yl[1] - 2.5, text,
            ha="center", va="top", fontsize=12, fontweight="bold", color=NAVY)


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    plt.close(fig)
    print("그림:", name)


# ---------------------------------------------------------------- 1. 서두 개념도
def msa_overview():
    fig, ax = canvas(10.4, 6.4)
    title(ax, "MSA 로그인 게시판 한눈에 보기")

    # 브라우저
    box(ax, 1, 25, 15, 15, "브라우저\n\nReact\nlocalhost:5173", "cyan", 10, bold=False)
    # 게이트웨이
    box(ax, 23, 17, 19, 31, "\n:8080\n\n모든 요청의 정문\n\n① 라우팅 (길 안내)\n② 로그인 토큰 검사\n③ CORS", "orange", 9.5)
    ax.text(32.5, 44.2, "API Gateway", ha="center", fontsize=10.5, fontweight="bold", color=ORANGE)
    # 서비스
    box(ax, 57, 37, 20, 15, "user-service  :8081\n\n회원가입 · 로그인\nJWT 토큰 발급", "navy", 9.5)
    box(ax, 57, 9, 20, 15, "post-service  :8082\n\n게시글 CRUD\n본인 글 검사(403)", "green", 9.5)
    # DB 컨테이너
    box(ax, 84, 4, 19, 52, "", "grey", dashed=True)
    note(ax, 93.5, 52.5, "PostgreSQL 컨테이너 1개", "#374151", 8.8, bold=True)
    note(ax, 93.5, 49.2, "mas-db  (localhost:5435)", GREY, 8.3)
    box(ax, 86.5, 34, 14, 11, "userdb\n─────\nusers", "navy", 9.5)
    box(ax, 86.5, 10, 14, 11, "postdb\n─────\nposts", "green", 9.5)

    # 화살표
    arrow(ax, 16.4, 32.5, 22.6, 32.5, "", NAVY)
    note(ax, 19.5, 36.5, "/api/...", NAVY, 8.3)
    note(ax, 8.5, 21, "React 는 8080\n하나만 안다", GREY, 8)
    arrow(ax, 42.4, 38, 56.6, 44, "/api/auth/**", NAVY, size=8.3, ly=2.5)
    arrow(ax, 42.4, 27, 56.6, 17, "/api/posts/**\n+ X-User-Id", GREEN, size=8.3, ly=-3)
    arrow(ax, 77.4, 44.5, 86.1, 40, "", NAVY)
    arrow(ax, 77.4, 16.5, 86.1, 15.5, "", GREEN)

    # 서비스끼리 / DB 끼리 막힘 표시
    note(ax, 67, 30.5, "× 서로의 코드 · DB 를\n직접 쓰지 않는다", RED, 8, bold=True)
    note(ax, 93.5, 27.5, "× FK · JOIN 불가\n(서로 다른 DB)", RED, 8, bold=True)

    # 아래 요약
    note(ax, 52, 0.5,
         "MSA 핵심 ① 업무별로 작은 서비스  ② 서비스마다 자기 DB (Database per Service)  "
         "③ 정문(Gateway)에서 한 번 인증", NAVY, 9, bold=True)
    save(fig, "fig_msa_overview.png")


# ---------------------------------------------------------------- 2. 모놀리식 vs MSA
def monolith_vs_msa():
    fig, ax = canvas(10.4, 5.2)
    # 왼쪽: 모놀리식
    note(ax, 22, 49, "모놀리식 (React 심화 과정의 서버)", NAVY, 11, bold=True)
    box(ax, 3, 18, 38, 26, "", "navy")
    note(ax, 22, 41, "Spring Boot 서버 1개  :8080", NAVY, 9.5, bold=True)
    box(ax, 5.5, 26, 10, 10, "회원\n(auth)", "white", 9)
    box(ax, 17, 26, 10, 10, "게시글\n(post)", "white", 9)
    box(ax, 28.5, 26, 10, 10, "보안\n(Security\n+JWT)", "white", 8.5)
    note(ax, 22, 21.5, "한 프로그램 · 한 번에 배포 · 하나가 죽으면 모두 멈춤", GREY, 8)
    box(ax, 12, 2, 20, 10, "DB authboard\nusers ─FK─ posts", "grey", 9)
    arrow(ax, 22, 17.6, 22, 12.4, "", NAVY)

    ax.plot([50, 50], [3, 50], color="#d1d5db", lw=1.2)
    ax.annotate("", xy=(56, 26), xytext=(46, 26),
                arrowprops=dict(arrowstyle="simple", fc=ORANGE, ec="none", mutation_scale=28))
    note(ax, 51, 31, "나누기", ORANGE, 9.5, bold=True)

    # 오른쪽: MSA
    note(ax, 80, 49, "MSA (이 교안)", "#1f9e93", 11, bold=True)
    box(ax, 66, 37, 28, 8, "API Gateway  :8080", "orange", 9.5)
    box(ax, 58, 19, 19, 11, "user-service\n:8081", "navy", 9)
    box(ax, 83, 19, 19, 11, "post-service\n:8082", "green", 9)
    arrow(ax, 74, 36.6, 68, 30.4, "", NAVY)
    arrow(ax, 86, 36.6, 92, 30.4, "", GREEN)
    box(ax, 60, 3, 15, 9, "userdb\nusers", "grey", 9)
    box(ax, 85, 3, 15, 9, "postdb\nposts", "grey", 9)
    arrow(ax, 67.5, 18.6, 67.5, 12.4, "", NAVY)
    arrow(ax, 92.5, 18.6, 92.5, 12.4, "", GREEN)
    note(ax, 80, 15.5, "따로 켜고 · 따로 고치고\n하나가 죽어도 나머지는 동작", GREY, 8)
    save(fig, "fig_monolith_vs_msa.png")


# ---------------------------------------------------------------- 3. DB 나누기 (FK → 복사)
def db_split():
    fig, ax = canvas(10.4, 4.8)
    note(ax, 22, 45, "모놀리식: DB 하나, 외래 키(FK)로 연결", NAVY, 10.5, bold=True)
    box(ax, 2, 4, 40, 36, "", "grey", dashed=True)
    note(ax, 22, 37.5, "authboard", GREY, 9, bold=True)
    box(ax, 4, 9, 15, 24, "users\n─────────\nid\nusername\npassword_hash\nnickname", "navy", 8.8)
    box(ax, 25, 9, 15, 24, "posts\n─────────\nid\nuser_id (FK)\ntitle\ncontent", "green", 8.8)
    arrow(ax, 24.6, 18, 19.4, 22, "FK", RED, size=8.5, ly=1.8)
    note(ax, 22, 6.2, "글 목록 = posts JOIN users (닉네임)", GREY, 8)

    ax.annotate("", xy=(55, 22), xytext=(46, 22),
                arrowprops=dict(arrowstyle="simple", fc=ORANGE, ec="none", mutation_scale=28))

    note(ax, 80, 45, "MSA: DB 두 개, 번호와 닉네임을 복사", "#1f9e93", 10.5, bold=True)
    box(ax, 58, 4, 19, 36, "", "grey", dashed=True)
    box(ax, 82, 4, 20, 36, "", "grey", dashed=True)
    note(ax, 67.5, 37.5, "userdb", GREY, 9, bold=True)
    note(ax, 92, 37.5, "postdb", GREY, 9, bold=True)
    box(ax, 60, 9, 15, 24, "users\n─────────\nid\nusername\npassword_hash\nnickname", "navy", 8.8)
    box(ax, 84, 9, 16, 24, "posts\n─────────\nid\nuser_id  ← 그냥 숫자\nwriter   ← 닉네임 복사\ntitle\ncontent", "green", 8.3)
    ax.plot([79.5, 79.5], [10, 32], color=RED, lw=1.4, ls=":")
    note(ax, 79.5, 21, "×", RED, 13, bold=True)
    note(ax, 80, 1.2, "FK · JOIN 대신, 글을 쓸 때 토큰 속 번호와 닉네임을 posts 에 함께 저장", GREY, 8)
    save(fig, "fig_db_split.png")


# ---------------------------------------------------------------- 4. 요청 흐름 (로그인 → 글쓰기)
def request_flow():
    fig, ax = canvas(10.4, 7.4)
    title(ax, "요청 흐름: 로그인 → 글쓰기")
    cols = [(9, "React", "cyan"), (32, "API Gateway\n:8080", "orange"), (56, "user-service\n:8081", "navy"),
            (78, "post-service\n:8082", "green"), (97, "PostgreSQL\nuserdb / postdb", "grey")]
    for x, name, color in cols:
        box(ax, x - 8, 58, 16, 8, name, color, 8.6)
        ax.plot([x, x], [2, 57.5], color="#cbd5e1", lw=1.2, ls="--", zorder=0)

    def msg(y, x1, x2, text, color=NAVY, dashed=False, size=8.2):
        arrow(ax, x1, y, x2, y, text, color, size=size, ly=2.2, dashed=dashed)

    note(ax, 1, 54, "① 로그인", NAVY, 9.5, ha="left", bold=True)
    msg(50, 9, 32, "POST /api/auth/login")
    msg(45, 32, 56, "그대로 전달 (로그인은 누구나)")
    msg(40, 56, 97, "SELECT users (userdb)")
    note(ax, 57, 35.5, "비밀번호 확인 → JWT 발급 (sub=1, nickname=민수)", NAVY, 7.8, ha="left")
    msg(31, 56, 9, "{ access_token, user }", NAVY, dashed=True)

    note(ax, 1, 26.5, "② 글쓰기", GREEN, 9.5, ha="left", bold=True)
    msg(22, 9, 32, "POST /api/posts\nAuthorization: Bearer 토큰", GREEN, size=7.8)
    note(ax, 31, 15, "토큰 검사 (같은 비밀 열쇠)\n→ X-User-Id: 1\n→ X-User-Nickname: 민수", ORANGE, 7.8, ha="right")
    msg(12, 32, 78, "헤더를 붙여 전달 (user-service 는 거치지 않음)", GREEN, size=7.8)
    msg(7.5, 78, 97, "INSERT posts\n(user_id=1, writer='민수')", GREEN, size=7.4)
    msg(3, 78, 9, "201 { id, user_id, writer, ... }", GREEN, dashed=True, size=7.8)
    save(fig, "fig_request_flow.png")


# ---------------------------------------------------------------- 5. 게이트웨이 AuthFilter 순서도
def auth_filter():
    fig, ax = canvas(10.4, 4.4)
    title(ax, "AuthFilter: 게이트웨이를 지나는 모든 요청")
    box(ax, 1, 20, 13, 10, "요청 도착", "cyan", 9.5)
    box(ax, 18, 20, 17, 10, "① 손님이 보낸\nX-User-* 헤더 지우기\n(위조 방지)", "orange", 8.5)
    box(ax, 39, 20, 17, 10, "② Authorization 의\n토큰 검사\n(서명 · 만료)", "orange", 8.5)
    box(ax, 60, 20, 17, 10, "③ 로그인 필요한\n주소인데 토큰이\n없거나 틀렸나?", "orange", 8.5)
    box(ax, 56.5, 1, 24, 10, "401 바로 돌려보냄\n{ \"detail\": \"로그인이 필요합니다\" }", "red", 7.8)
    box(ax, 82, 20, 20, 10, "④ 토큰 OK 면\nX-User-Id,\nX-User-Nickname 붙여\n서비스로 전달", "green", 8.2)
    arrow(ax, 14.4, 25, 17.6, 25)
    arrow(ax, 35.4, 25, 38.6, 25)
    arrow(ax, 56.4, 25, 59.6, 25)
    arrow(ax, 68.5, 19.6, 68.5, 11.4, "예", RED, size=8.5, lx=3)
    arrow(ax, 77.4, 25, 81.6, 25, "", GREEN)
    note(ax, 79.5, 33, "아니오", GREEN, 8.5)
    note(ax, 93, 6, "로그인 없이 되는 주소\nGET /api/posts/**\nPOST /api/auth/signup, login", GREY, 8)
    save(fig, "fig_auth_filter.png")


# ---------------------------------------------------------------- 6. 장애 격리 실험
def failure():
    fig, ax = canvas(10.4, 4.0)
    title(ax, "실험: user-service 를 끄면?")
    box(ax, 2, 14, 15, 12, "React\n(이미 로그인함)", "cyan", 9)
    box(ax, 25, 14, 17, 12, "API Gateway\n:8080", "orange", 9)
    box(ax, 52, 24, 20, 10, "user-service  :8081\n■ 꺼짐", "red", 9)
    box(ax, 52, 4, 20, 10, "post-service  :8082\n● 켜짐", "green", 9)
    arrow(ax, 17.4, 20, 24.6, 20)
    arrow(ax, 42.4, 23, 51.6, 28, "", RED, dashed=True)
    arrow(ax, 42.4, 17, 51.6, 10, "", GREEN)
    note(ax, 86, 29, "로그인 · 회원가입 · 내 정보\n→ 실패 (503)", RED, 9, bold=True)
    note(ax, 86, 9, "글 목록 · 읽기 · 쓰기 · 수정 · 삭제\n→ 정상 동작!", GREEN, 9, bold=True)
    note(ax, 50, 0.5, "토큰 검사는 게이트웨이가, 글 저장은 post-service 가 하므로 회원 서비스가 없어도 글 기능은 살아 있다 (장애 격리)",
         GREY, 8)
    save(fig, "fig_failure.png")


if __name__ == "__main__":
    msa_overview()
    monolith_vs_msa()
    db_split()
    request_flow()
    auth_filter()
    failure()
