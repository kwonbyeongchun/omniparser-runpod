"""
OmniParser v2 RunPod Serverless 엔드포인트 테스트 스크립트
로컬 PC에서 실행하여 RunPod 엔드포인트를 테스트
"""

import base64
import json
import sys
import time
import requests

# --- 설정 ---
RUNPOD_API_KEY = "rpa_G05IZNUHJPG3RPCPQQ2FQ4CYFHT752SWXSOWNFFK1kxcod"
ENDPOINT_ID = ""  # RunPod에서 엔드포인트 생성 후 ID 입력

BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json",
}


def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def run_sync(payload: dict) -> dict:
    """동기 호출 (최대 30초 대기)"""
    resp = requests.post(f"{BASE_URL}/runsync", headers=HEADERS, json={"input": payload}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def run_async(payload: dict) -> dict:
    """비동기 호출 → 폴링으로 결과 대기"""
    resp = requests.post(f"{BASE_URL}/run", headers=HEADERS, json={"input": payload}, timeout=30)
    resp.raise_for_status()
    job = resp.json()
    job_id = job["id"]
    print(f"Job submitted: {job_id}")

    # 폴링
    while True:
        status_resp = requests.get(f"{BASE_URL}/status/{job_id}", headers=HEADERS, timeout=30)
        status_resp.raise_for_status()
        result = status_resp.json()

        status = result.get("status")
        print(f"  Status: {status}")

        if status == "COMPLETED":
            return result
        elif status in ("FAILED", "CANCELLED", "TIMED_OUT"):
            print(f"  Job failed: {result}")
            return result

        time.sleep(3)


def test_basic(image_path: str):
    """기본 동작 테스트"""
    print("\n=== 기본 동작 테스트 ===")
    payload = {"image": image_to_base64(image_path)}

    start = time.time()
    result = run_async(payload)
    elapsed = time.time() - start

    output = result.get("output", {})
    elements = output.get("elements", [])
    ocr_text = output.get("ocr_text", [])
    error = output.get("error")

    if error:
        print(f"  ERROR: {error}")
        return

    print(f"  응답 시간: {elapsed:.1f}초")
    print(f"  감지된 요소 수: {len(elements)}")
    print(f"  OCR 텍스트 수: {len(ocr_text)}")

    for elem in elements[:5]:
        print(f"    - [{elem.get('id')}] {elem.get('content', '')[:80]}")

    if ocr_text:
        print(f"  OCR 샘플: {ocr_text[:5]}")


def test_korean_ocr(image_path: str):
    """한국어 OCR 테스트"""
    print("\n=== 한국어 OCR 테스트 ===")
    payload = {"image": image_to_base64(image_path)}

    result = run_async(payload)
    output = result.get("output", {})
    ocr_text = output.get("ocr_text", [])
    error = output.get("error")

    if error:
        print(f"  ERROR: {error}")
        return

    print(f"  OCR 인식 텍스트:")
    for text in ocr_text:
        print(f"    - {text}")

    # 한국어 포함 여부 확인
    has_korean = any(any("\uac00" <= c <= "\ud7a3" for c in t) for t in ocr_text)
    print(f"  한국어 인식: {'성공' if has_korean else '실패'}")


def test_error_handling():
    """에러 처리 테스트"""
    print("\n=== 에러 처리 테스트 ===")

    # 빈 입력
    print("  [빈 이미지 테스트]")
    result = run_async({})
    output = result.get("output", {})
    print(f"    결과: {output}")

    # 잘못된 base64
    print("  [잘못된 base64 테스트]")
    result = run_async({"image": "not-valid-base64!!!"})
    output = result.get("output", {})
    print(f"    결과: {output}")


if __name__ == "__main__":
    if not ENDPOINT_ID:
        print("ENDPOINT_ID를 설정해주세요.")
        print("RunPod에서 Serverless Endpoint 생성 후 ID를 입력하세요.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("사용법:")
        print("  python test_api.py <image_path>          # 기본 테스트")
        print("  python test_api.py <image_path> --korean  # 한국어 OCR 테스트")
        print("  python test_api.py --error                # 에러 처리 테스트")
        sys.exit(1)

    if sys.argv[1] == "--error":
        test_error_handling()
    else:
        image_path = sys.argv[1]
        test_basic(image_path)

        if len(sys.argv) > 2 and sys.argv[2] == "--korean":
            test_korean_ocr(image_path)
