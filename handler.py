"""
OmniParser v2 RunPod Serverless Handler
스크린샷 이미지를 받아 UI 요소 파싱 + 한국어/영어 OCR 결과를 반환
"""

import base64
import io
import json
import torch
import numpy as np
from PIL import Image

import runpod

# --- 전역 모델 (cold start 시 1회 로딩) ---
yolo_model = None
caption_model_processor = None
paddle_ocr = None

WEIGHTS_DIR = "/app/OmniParser/weights"


def load_models():
    """모델을 전역으로 로딩 (warm 상태에서 재사용)"""
    global yolo_model, caption_model_processor, paddle_ocr

    import sys
    sys.path.insert(0, "/app/OmniParser")

    from util.utils import get_yolo_model, get_caption_model_processor
    from paddleocr import PaddleOCR

    # YOLOv8 아이콘 감지 모델
    yolo_model = get_yolo_model(model_path=f"{WEIGHTS_DIR}/icon_detect/model.pt")

    # Florence-2 캡셔닝 모델
    caption_model_processor = get_caption_model_processor(
        model_name="florence2",
        model_name_or_path=f"{WEIGHTS_DIR}/icon_caption_florence",
    )

    # PaddleOCR 한국어 + 영어
    paddle_ocr = PaddleOCR(
        lang="korean",
        use_angle_cls=False,
        use_gpu=False,
    )

    print("All models loaded successfully.")


def handler(event):
    """
    RunPod Serverless 핸들러

    입력:
        {
            "image": "<base64 encoded image>",
            "box_threshold": 0.05,    # optional
            "iou_threshold": 0.1,     # optional
            "imgsz": 1920             # optional
        }

    출력:
        {
            "labeled_image": "<base64 encoded labeled image>",
            "elements": [
                {
                    "id": 0,
                    "bbox": [x1, y1, x2, y2],
                    "content": "텍스트 또는 아이콘 설명"
                },
                ...
            ]
        }
    """
    import sys
    sys.path.insert(0, "/app/OmniParser")
    from util.utils import check_ocr_box, get_som_labeled_img

    job_input = event["input"]

    # 입력 검증
    image_b64 = job_input.get("image")
    if not image_b64:
        return {"error": "image field is required (base64 encoded)"}

    box_threshold = job_input.get("box_threshold", 0.05)
    iou_threshold = job_input.get("iou_threshold", 0.1)
    imgsz = job_input.get("imgsz", 1920)

    try:
        # base64 → PIL Image
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # 임시 파일로 저장 (check_ocr_box가 파일 경로도 지원)
        temp_path = "/tmp/input_image.png"
        image.save(temp_path)

        # OCR 수행 (PaddleOCR 한국어)
        ocr_result = check_ocr_box(
            temp_path,
            display_img=False,
            output_bb_format="xyxy",
            use_paddleocr=True,
        )
        text, ocr_bbox = ocr_result[0]

        # SOM 라벨링 (YOLOv8 + Florence-2 + OCR bbox)
        labeled_img_b64, label_coordinates, parsed_content = get_som_labeled_img(
            temp_path,
            model=yolo_model,
            BOX_TRESHOLD=box_threshold,
            output_coord_in_ratio=True,
            ocr_bbox=ocr_bbox,
            iou_threshold=iou_threshold,
            caption_model_processor=caption_model_processor,
            use_local_semantics=True,
        )

        # 결과 구성
        elements = []
        if parsed_content:
            for i, content in enumerate(parsed_content):
                element = {
                    "id": i,
                    "content": content,
                }
                if label_coordinates and str(i) in label_coordinates:
                    element["bbox"] = label_coordinates[str(i)]
                elements.append(element)

        return {
            "labeled_image": labeled_img_b64,
            "elements": elements,
            "ocr_text": text,
        }

    except Exception as e:
        return {"error": str(e)}


# 모델 로딩 (컨테이너 시작 시 1회)
load_models()

# RunPod Serverless 시작
runpod.serverless.start({"handler": handler})
