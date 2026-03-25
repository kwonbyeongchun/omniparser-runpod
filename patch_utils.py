"""
OmniParser utils.py 패치 스크립트
filtered_boxes가 list of list일 때 dict로 변환하여 호환성 확보
"""
import re

filepath = "/app/OmniParser/util/utils.py"

with open(filepath, "r") as f:
    content = f.read()

# remove_overlap_new 반환값이 list of list일 경우 dict로 변환하는 코드 삽입
# 원본: filtered_boxes = remove_overlap_new(...)
# 패치: 반환값을 검사하고 list of list면 dict로 변환
old = "filtered_boxes = remove_overlap_new(boxes=xyxy_elem, iou_threshold=iou_threshold, ocr_bbox=ocr_bbox_elem)"
new = """filtered_boxes = remove_overlap_new(boxes=xyxy_elem, iou_threshold=iou_threshold, ocr_bbox=ocr_bbox_elem)
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

if old in content:
    content = content.replace(old, new)
    print("Patch 1 applied: filtered_boxes dict conversion")
else:
    print("WARNING: Patch 1 target not found")

# Patch 2: ocr_text가 None일 때 빈 리스트로 대체
old2 = "ocr_bbox_elem = [{'type': 'text', 'bbox':box, 'interactivity':False, 'content':txt, 'source': 'box_ocr_content_ocr'} for box, txt in zip(ocr_bbox, ocr_text) if int_box_area(box, w, h) > 0]"
new2 = """ocr_bbox = ocr_bbox if ocr_bbox is not None else []
    ocr_text = ocr_text if ocr_text is not None else []
    ocr_bbox_elem = [{'type': 'text', 'bbox':box, 'interactivity':False, 'content':txt, 'source': 'box_ocr_content_ocr'} for box, txt in zip(ocr_bbox, ocr_text) if int_box_area(box, w, h) > 0]"""

if old2 in content:
    content = content.replace(old2, new2)
    print("Patch 2 applied: ocr_bbox/ocr_text None guard")
else:
    print("WARNING: Patch 2 target not found")

with open(filepath, "w") as f:
    f.write(content)
print("All patches done.")
