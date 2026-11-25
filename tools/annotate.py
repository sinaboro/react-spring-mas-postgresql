"""annotate.py - 교안 화면 캡처에 "여기를 보세요" 분홍 상자를 그린다.

    python tools/annotate.py            # tools/annot_base/*.jpg (상자 없는 원본) → docs/images/*.jpg (상자 그린 것)
    python tools/annotate.py --sheet    # 확인용으로 모든 결과를 한 장씩 모은 미리보기도 만든다

원본(annot_base)은 고치지 않는다. 상자 위치를 바꾸려면 아래 BOXES 의 좌표만 고치고 다시 실행한다.
좌표는 원본 그림의 픽셀 (왼쪽, 위, 오른쪽, 아래).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "tools" / "annot_base"
OUT = ROOT / "docs" / "images"
PINK = (255, 32, 140)

# 그림 → 강조할 상자 목록 (좌표는 원본 그림의 픽셀)
BOXES = {'d1_list_before.png': [(920, 240, 1060, 425)],
 'd2_profile.png': [(1120, 28, 1240, 78), (458, 553, 1042, 702)],
 'd3_list_after.png': [(1120, 28, 1240, 78), (920, 240, 1060, 425)],
 'j01_idea_home.png': [(242, 42, 335, 77)],
 'j02_open_dialog.png': [(244, 200, 850, 232), (740, 485, 838, 518)],
 'j03_trust.png': [(58, 124, 424, 154), (249, 186, 361, 222)],
 'j04_project_tree.png': [(64, 113, 155, 144), (64, 159, 157, 190), (64, 183, 157, 214)],
 'j05_gradle_panel.png': [(10, 76, 175, 200)],
 'j06_file_menu.png': [(32, 165, 270, 193)],
 'j07_project_structure.png': [(254, 168, 716, 204)],
 'j08_sdk_dropdown.png': [(72, 51, 444, 79), (72, 78, 244, 104)],
 'j09_app_class.png': [(108, 429, 225, 455), (358, 322, 390, 353)],
 'j10_run_menu.png': [(56, 41, 316, 69)],
 'j11_services_running.png': [(36, 80, 245, 147), (958, 226, 1502, 252)],
 's3_list_user.png': [(1140, 30, 1232, 80), (930, 250, 1060, 480)],
 's4_detail_owner.png': [(1172, 466, 1372, 526)],
 's5_detail_other.png': [(1266, 461, 1372, 526)],
 's6_docs_user.png': [(26, 396, 564, 448), (26, 767, 1472, 833)],
 's7_login_503.png': [(456, 284, 1044, 392)],
 'vs_terminal_cmd.jpg': [(1323, 6, 1377, 32), (12, 88, 163, 114)],
 'vs_terminal_profiles.jpg': [(15, 96, 165, 122), (15, 239, 165, 266), (245, 308, 280, 334)],
 'vs_terminal_ps.jpg': [(12, 38, 182, 64), (1304, 54, 1555, 84)],
 'vs_view_menu.jpg': [(150, 330, 362, 354)]}


def draw(name, boxes):
    im = Image.open(BASE / name).convert("RGB")
    d = ImageDraw.Draw(im)
    # 선 굵기: PDF 에 줄어 들어갈 비율을 계산해서 종이 위에서 약 2.6pt 가 되게 한다
    #   (build_guide 의 그림 폭: 본문 폭의 86% = 약 424pt, 단 원래 크기 × 0.55pt 를 넘지 않음)
    shown = min(424, im.width * 0.55)
    w = max(3, round(2.6 * im.width / shown))
    for x0, y0, x1, y1 in boxes:
        # 작은 상자는 선을 가늘게 (글자를 덮지 않게), 그리고 상자 바깥쪽으로 그린다
        bw = max(3, min(w, round(min(x1 - x0, y1 - y0) / 4)))
        g = bw // 2 + 2
        d.rounded_rectangle((x0 - g, y0 - g, x1 + g, y1 + g), radius=bw * 3, outline=PINK, width=bw)
    if name.endswith(".png"):
        im.save(OUT / name)
    else:
        im.save(OUT / name, quality=92)
    return im


def main():
    made = []
    for name, boxes in BOXES.items():
        if not (BASE / name).exists():
            print("원본 없음:", name)
            continue
        made.append((name, draw(name, boxes)))
    print(f"상자 그림 {len(made)}장")
    if "--sheet" in sys.argv:   # 확인용 미리보기 (6장씩 한 장)
        sheet_dir = ROOT / "tools" / "annot_preview"
        sheet_dir.mkdir(exist_ok=True)
        for k in range(0, len(made), 6):
            group = made[k:k + 6]
            thumbs = []
            for name, im in group:
                t = im.copy()
                t.thumbnail((760, 420))
                thumbs.append(t)
            sheet = Image.new("RGB", (1540, 3 * 440), "white")
            for i, t in enumerate(thumbs):
                sheet.paste(t, ((i % 2) * 770, (i // 2) * 440))
            sheet.save(sheet_dir / f"sheet{k // 6}.jpg", quality=85)


if __name__ == "__main__":
    main()
