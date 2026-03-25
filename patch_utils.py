"""
OmniParser utils.py 패치 스크립트
- easyocr import → mock 교체 (PaddleOCR만 사용하므로 easyocr 불필요)
- PaddleOCR 한국어로 변경
- filtered_boxes list of list → dict 변환
- ocr_bbox/ocr_text None guard
"""

filepath = "/app/OmniParser/util/utils.py"

with open(filepath, "r") as f:
    content = f.read()

# Patch 0-pre: openai import 제거 (설치되지 않은 패키지)
old_openai = "from openai import AzureOpenAI"
new_openai = "# from openai import AzureOpenAI  # PATCHED: removed (not installed)"
if old_openai in content:
    content = content.replace(old_openai, new_openai)
    print("Patch 0-pre applied: openai import removed")

# Patch 0: easyocr import 및 reader 생성을 mock으로 교체
old0 = "import easyocr"
new0 = "# import easyocr  # PATCHED: removed (using PaddleOCR only)"
if old0 in content:
    content = content.replace(old0, new0)
    print("Patch 0a applied: easyocr import removed")

old0b = "reader = easyocr.Reader(['en'])"
new0b = "reader = None  # PATCHED: easyocr reader removed"
if old0b in content:
    content = content.replace(old0b, new0b)
    print("Patch 0b applied: easyocr reader removed")

# Patch 1: PaddleOCR 한국어로 변경
old1 = """paddle_ocr = PaddleOCR(
    lang='en',
    use_angle_cls=False,
    use_gpu=False,
    show_log=False,
    max_batch_size=1024,
    use_dilation=True,
    det_db_score_mode='slow',
)"""
new1 = """paddle_ocr = PaddleOCR(
    lang='korean',
    use_angle_cls=False,
    use_gpu=False,
    show_log=False,
    max_batch_size=1024,
    use_dilation=True,
    det_db_score_mode='slow',
)"""

if old1 in content:
    content = content.replace(old1, new1)
    print("Patch 1 applied: PaddleOCR lang=korean")
else:
    print("WARNING: Patch 1 target not found")

# Patch 2: filtered_boxes dict 변환
old2 = "filtered_boxes = remove_overlap_new(boxes=xyxy_elem, iou_threshold=iou_threshold, ocr_bbox=ocr_bbox_elem)"
new2 = """filtered_boxes = remove_overlap_new(boxes=xyxy_elem, iou_threshold=iou_threshold, ocr_bbox=ocr_bbox_elem)
    # PATCH: filtered_boxes가 list of list일 경우 dict로 변환
    if filtered_boxes and not isinstance(filtered_boxes[0], dict):
        patched = []
        for box in filtered_boxes:
            if isinstance(box, dict):
                patched.append(box)
            elif isinstance(box, (list, tuple)):
                patched.append({'type': 'icon', 'bbox': list(box), 'content': None})
            else:
                patched.append({'type': 'icon', 'bbox': [0,0,0,0], 'content': None})
        filtered_boxes = patched"""

if old2 in content:
    content = content.replace(old2, new2)
    print("Patch 2 applied: filtered_boxes dict conversion")
else:
    print("WARNING: Patch 2 target not found")

# Patch 3: ocr_bbox/ocr_text None guard
old3 = "ocr_bbox_elem = [{'type': 'text', 'bbox':box, 'interactivity':False, 'content':txt, 'source': 'box_ocr_content_ocr'} for box, txt in zip(ocr_bbox, ocr_text) if int_box_area(box, w, h) > 0]"
new3 = """ocr_bbox = ocr_bbox if ocr_bbox is not None else []
    ocr_text = ocr_text if ocr_text is not None else []
    ocr_bbox_elem = [{'type': 'text', 'bbox':box, 'interactivity':False, 'content':txt, 'source': 'box_ocr_content_ocr'} for box, txt in zip(ocr_bbox, ocr_text) if int_box_area(box, w, h) > 0]"""

if old3 in content:
    content = content.replace(old3, new3)
    print("Patch 3 applied: ocr_bbox/ocr_text None guard")
else:
    print("WARNING: Patch 3 target not found")

with open(filepath, "w") as f:
    f.write(content)
print("All patches done.")
