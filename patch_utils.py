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
    with open(filepath, "w") as f:
        f.write(content)
    print("Patch applied successfully.")
else:
    print("WARNING: Could not find target code to patch. Searching for alternatives...")
    # 대체 패턴 검색
    if "remove_overlap_new" in content:
        print("remove_overlap_new found but pattern mismatch. Manual review needed.")
    else:
        print("remove_overlap_new not found in utils.py")
