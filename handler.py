"""
OmniParser v2 RunPod Serverless Handler - 디버그 모드
단계별로 import/로딩을 테스트하여 어디서 실패하는지 확인
"""
import sys
print("Step 0: handler.py started", flush=True)

try:
    print("Step 1: importing runpod...", flush=True)
    import runpod
    print("Step 1: OK", flush=True)
except Exception as e:
    print(f"Step 1 FAILED: {e}", flush=True)
    sys.exit(1)

try:
    print("Step 2: importing torch...", flush=True)
    import torch
    print(f"Step 2: OK (torch {torch.__version__}, cuda={torch.cuda.is_available()})", flush=True)
except Exception as e:
    print(f"Step 2 FAILED: {e}", flush=True)

try:
    print("Step 3: importing OmniParser utils...", flush=True)
    sys.path.insert(0, "/app/OmniParser")
    from util.utils import get_yolo_model, get_caption_model_processor
    print("Step 3: OK", flush=True)
except Exception as e:
    print(f"Step 3 FAILED: {e}", flush=True)

try:
    print("Step 4: importing paddleocr...", flush=True)
    from paddleocr import PaddleOCR
    print("Step 4: OK", flush=True)
except Exception as e:
    print(f"Step 4 FAILED: {e}", flush=True)

try:
    print("Step 5: loading YOLO model...", flush=True)
    yolo_model = get_yolo_model(model_path="/app/OmniParser/weights/icon_detect/model.pt")
    print("Step 5: OK", flush=True)
except Exception as e:
    print(f"Step 5 FAILED: {e}", flush=True)
    yolo_model = None

try:
    print("Step 6: loading Florence-2 model...", flush=True)
    caption_model_processor = get_caption_model_processor(
        model_name="florence2",
        model_name_or_path="/app/OmniParser/weights/icon_caption_florence",
    )
    print("Step 6: OK", flush=True)
except Exception as e:
    print(f"Step 6 FAILED: {e}", flush=True)
    caption_model_processor = None

try:
    print("Step 7: loading PaddleOCR korean...", flush=True)
    paddle_ocr = PaddleOCR(
        lang="korean",
        use_angle_cls=False,
        use_gpu=False,
        show_log=False,
    )
    print("Step 7: OK", flush=True)
except Exception as e:
    print(f"Step 7 FAILED: {e}", flush=True)
    paddle_ocr = None

print("All steps done. Starting serverless handler...", flush=True)


def handler(event):
    return {"status": "ok", "message": "handler is working"}


runpod.serverless.start({"handler": handler})
