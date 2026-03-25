"""
OmniParser v2 RunPod Serverless Handler
스크린샷 이미지를 받아 UI 요소 파싱 + 한국어/영어 OCR 결과를 반환
"""
import sys
import base64
import io
import traceback

import torch
import numpy as np
from PIL import Image
import runpod

sys.path.insert(0, "/app/OmniParser")

# --- 모델 로딩 (cold start 시 1회) ---
print("Loading models...", flush=True)

from util.utils import get_yolo_model, get_caption_model_processor, check_ocr_box, get_som_labeled_img
from paddleocr import PaddleOCR

WEIGHTS_DIR = "/app/OmniParser/weights"

yolo_model = get_yolo_model(model_path=f"{WEIGHTS_DIR}/icon_detect/model.pt")
print("YOLO model loaded.", flush=True)

caption_model_processor = get_caption_model_processor(
    model_name="florence2",
    model_name_or_path=f"{WEIGHTS_DIR}/icon_caption_florence",
)
print("Florence-2 model loaded.", flush=True)

paddle_ocr = PaddleOCR(
    lang="korean",
    use_angle_cls=False,
    use_gpu=False,
    show_log=False,
)
print("PaddleOCR loaded.", flush=True)
print("All models ready.", flush=True)


def handle_ocr(image_b64):
    """PaddleOCR만 실행하여 텍스트 + 바운딩박스 반환"""
    image_bytes = base64.b64decode(image_b64)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    temp_path = "/tmp/input_image.png"
    image.save(temp_path)

    result = paddle_ocr.ocr(temp_path, cls=False)

    ocr_items = []
    if result and result[0]:
        for line in result[0]:
            bbox = line[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            text = line[1][0]
            confidence = line[1][1]
            # 4점 좌표 → xyxy 변환
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            ocr_items.append({
                "text": text,
                "confidence": round(confidence, 4),
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
            })

    return {
        "ocr_items": ocr_items,
        "ocr_text": [item["text"] for item in ocr_items],
    }


def handle_detect(image_b64, box_threshold, iou_threshold):
    """YOLO + Florence-2만 실행 (OCR 제외)"""
    image_bytes = base64.b64decode(image_b64)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    temp_path = "/tmp/input_image.png"
    image.save(temp_path)

    # SOM 라벨링 (YOLOv8 + Florence-2, OCR bbox 없이)
    labeled_img_b64, label_coordinates, parsed_content = get_som_labeled_img(
        temp_path,
        model=yolo_model,
        BOX_TRESHOLD=box_threshold,
        output_coord_in_ratio=True,
        ocr_bbox=None,
        iou_threshold=iou_threshold,
        caption_model_processor=caption_model_processor,
        use_local_semantics=True,
    )

    elements = []
    if parsed_content:
        for i, content in enumerate(parsed_content):
            element = {"id": i, "content": content}
            if label_coordinates:
                if isinstance(label_coordinates, dict) and str(i) in label_coordinates:
                    element["bbox"] = label_coordinates[str(i)]
                elif isinstance(label_coordinates, list) and i < len(label_coordinates):
                    element["bbox"] = label_coordinates[i]
            elements.append(element)

    return {
        "labeled_image": labeled_img_b64,
        "elements": elements,
    }


def handle_full(image_b64, box_threshold, iou_threshold):
    """전체 OmniParser 실행 (YOLO + Florence-2 + OCR)"""
    image_bytes = base64.b64decode(image_b64)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    temp_path = "/tmp/input_image.png"
    image.save(temp_path)

    # OCR (PaddleOCR 한국어)
    ocr_result = check_ocr_box(
        temp_path,
        display_img=False,
        output_bb_format="xyxy",
        use_paddleocr=True,
    )
    text, ocr_bbox = ocr_result[0]

    # SOM 라벨링 (YOLOv8 + Florence-2 + OCR)
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
            element = {"id": i, "content": content}
            if label_coordinates:
                if isinstance(label_coordinates, dict) and str(i) in label_coordinates:
                    element["bbox"] = label_coordinates[str(i)]
                elif isinstance(label_coordinates, list) and i < len(label_coordinates):
                    element["bbox"] = label_coordinates[i]
            elements.append(element)

    return {
        "labeled_image": labeled_img_b64,
        "elements": elements,
        "ocr_text": text,
    }


def handler(event):
    job_input = event["input"]

    image_b64 = job_input.get("image")
    if not image_b64:
        return {"error": "image field is required (base64 encoded)"}

    mode = job_input.get("mode", "full")

    try:
        if mode == "ocr":
            return handle_ocr(image_b64)
        elif mode == "detect":
            box_threshold = job_input.get("box_threshold", 0.05)
            iou_threshold = job_input.get("iou_threshold", 0.1)
            return handle_detect(image_b64, box_threshold, iou_threshold)
        else:
            box_threshold = job_input.get("box_threshold", 0.05)
            iou_threshold = job_input.get("iou_threshold", 0.1)
            return handle_full(image_b64, box_threshold, iou_threshold)

    except Exception as e:
        tb = traceback.format_exc()
        print(f"Handler error: {tb}", flush=True)
        return {"error": str(e), "traceback": tb}


runpod.serverless.start({"handler": handler})
