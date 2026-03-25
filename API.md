# OmniParser v2 API 사용 설명서

## 개요

스크린샷 이미지를 전송하면 UI 요소(아이콘, 버튼, 텍스트 등)를 감지하고, 한국어/영어 OCR 결과를 반환하는 API입니다.

- **플랫폼**: RunPod Serverless
- **모델**: OmniParser v2 (YOLOv8 + Florence-2 + PaddleOCR)
- **OCR 언어**: 한국어 + 영어

## 엔드포인트 정보

| 항목 | 값 |
|---|---|
| Endpoint ID | `v5j0gr4r45ga58` |
| Base URL | `https://api.runpod.ai/v2/v5j0gr4r45ga58` |
| API Key | RunPod API Key (Authorization 헤더) |

## 인증

모든 요청에 Authorization 헤더가 필요합니다.

```
Authorization: Bearer <RUNPOD_API_KEY>
```

## API 엔드포인트

### 1. 비동기 요청 (권장)

작업을 큐에 넣고 Job ID를 즉시 반환합니다.

**POST** `/run`

#### 요청

```bash
curl -X POST "https://api.runpod.ai/v2/{ENDPOINT_ID}/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image": "<base64 encoded image>",
      "box_threshold": 0.05,
      "iou_threshold": 0.1
    }
  }'
```

#### 입력 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `image` | string | **필수** | - | Base64 인코딩된 이미지 (PNG, JPG 등) |
| `mode` | string | 선택 | `"full"` | `"full"`: 전체 파싱, `"detect"`: UI 요소 감지만, `"ocr"`: OCR만 |
| `box_threshold` | float | 선택 | 0.05 | UI 요소 감지 신뢰도 임계값 (full, detect 모드) |
| `iou_threshold` | float | 선택 | 0.1 | 중복 박스 제거 임계값 (full, detect 모드) |

#### 응답

```json
{
  "id": "job-id-here",
  "status": "IN_QUEUE"
}
```

### 2. 결과 조회

Job ID로 결과를 조회합니다.

**GET** `/status/{job_id}`

```bash
curl "https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{JOB_ID}" \
  -H "Authorization: Bearer $RUNPOD_API_KEY"
```

#### 응답 (처리 중)

```json
{
  "id": "job-id",
  "status": "IN_QUEUE"
}
```

#### 응답 (완료 - full 모드)

```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "delayTime": 5000,
  "executionTime": 7000,
  "output": {
    "elements": [...],
    "ocr_text": [...]
  }
}
```

#### 응답 (완료 - detect 모드)

```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "delayTime": 5000,
  "executionTime": 4800,
  "output": {
    "elements": [
      {
        "id": 0,
        "bbox": [0.05, 0.08, 0.09, 0.12],
        "content": {
          "type": "icon",
          "bbox": [0.05, 0.08, 0.09, 0.12],
          "content": "Microsoft Word."
        }
      }
    ]
  }
}
```

#### 응답 (완료 - OCR 모드)

```json
{
  "id": "job-id",
  "status": "COMPLETED",
  "delayTime": 1000,
  "executionTime": 1500,
  "output": {
    "ocr_items": [
      {
        "text": "홈택스",
        "confidence": 0.9512,
        "bbox": [120, 45, 280, 78]
      },
      {
        "text": "Login",
        "confidence": 0.9834,
        "bbox": [300, 100, 400, 130]
      }
    ],
    "ocr_text": ["홈택스", "Login"]
  }
}
```

### 3. 동기 요청

결과가 나올 때까지 대기합니다. 타임아웃이 짧을 수 있으므로 비동기 방식 권장.

**POST** `/runsync`

요청 형식은 `/run`과 동일.

### 4. Health Check

워커 상태를 확인합니다.

**GET** `/health`

```bash
curl "https://api.runpod.ai/v2/{ENDPOINT_ID}/health" \
  -H "Authorization: Bearer $RUNPOD_API_KEY"
```

```json
{
  "jobs": {"completed": 5, "failed": 0, "inProgress": 1, "inQueue": 0, "retried": 0},
  "workers": {"idle": 1, "initializing": 0, "ready": 1, "running": 1, "throttled": 0, "unhealthy": 0}
}
```

### 5. 작업 취소

**POST** `/cancel/{job_id}`

```bash
curl -X POST "https://api.runpod.ai/v2/{ENDPOINT_ID}/cancel/{JOB_ID}" \
  -H "Authorization: Bearer $RUNPOD_API_KEY"
```

## 응답 상세

### output 필드 (mode=full, 기본값)

| 필드 | 타입 | 설명 |
|---|---|---|
| `elements` | array | 감지된 UI 요소 목록 |
| `ocr_text` | array | OCR로 인식된 텍스트 목록 |

### output 필드 (mode=detect)

| 필드 | 타입 | 설명 |
|---|---|---|
| `elements` | array | 감지된 UI 요소 목록 (아이콘/버튼만, 텍스트 제외) |

### output 필드 (mode=ocr)

| 필드 | 타입 | 설명 |
|---|---|---|
| `ocr_items` | array | OCR 결과 목록 (텍스트 + 좌표 + 신뢰도) |
| `ocr_text` | array | 인식된 텍스트만 추출한 목록 |

### ocr_items 배열 항목

```json
{
  "text": "홈택스",
  "confidence": 0.9512,
  "bbox": [x1, y1, x2, y2]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `text` | string | 인식된 텍스트 |
| `confidence` | float | 인식 신뢰도 (0.0~1.0) |
| `bbox` | array | 바운딩 박스 좌표 (픽셀) [x1, y1, x2, y2] |

### elements 배열 항목

```json
{
  "id": 0,
  "bbox": [x1, y1, x2, y2],
  "content": {
    "type": "icon",
    "bbox": [x1, y1, x2, y2],
    "content": "Close"
  }
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | int | 요소 번호 (0부터 시작) |
| `bbox` | array | 바운딩 박스 좌표 (비율, 0.0~1.0) [x1, y1, x2, y2] |
| `content.type` | string | 요소 유형 (`icon`, `text` 등) |
| `content.content` | string | 요소 설명 (영어). 예: "Close", "Refresh", "Microsoft Word" |

### bbox 좌표

좌표는 이미지 크기 대비 **비율**(0.0~1.0)로 반환됩니다.

```
실제 픽셀 좌표 = bbox 값 * 이미지 크기
예: bbox[0] * image_width = x1 픽셀
```

### 에러 응답

```json
{
  "status": "FAILED",
  "error": "에러 메시지",
  "output": {
    "error": "에러 메시지",
    "traceback": "상세 스택 트레이스"
  }
}
```

## 사용 예시

### Python

```python
import base64
import time
import requests

API_KEY = "rpa_xxxxx"
ENDPOINT_ID = "v5j0gr4r45ga58"
BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 이미지 → base64
with open("screenshot.png", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

# 비동기 요청
resp = requests.post(f"{BASE_URL}/run", headers=HEADERS, json={
    "input": {"image": image_b64}
})
job_id = resp.json()["id"]

# 폴링
while True:
    result = requests.get(f"{BASE_URL}/status/{job_id}", headers=HEADERS).json()
    if result["status"] == "COMPLETED":
        break
    elif result["status"] == "FAILED":
        print(f"Error: {result.get('error')}")
        break
    time.sleep(3)

# 결과
output = result["output"]
print(f"감지된 요소: {len(output['elements'])}개")
print(f"OCR 텍스트: {output['ocr_text']}")

# 결과 출력
for elem in output["elements"]:
    print(f"[{elem['id']}] {elem.get('content', '')}")
```

### curl

```bash
# 1. 이미지 base64 인코딩
IMG_B64=$(base64 -w0 screenshot.png)

# 2. 요청 파일 생성
printf '{"input": {"image": "' > req.json
echo -n "$IMG_B64" >> req.json
printf '"}}' >> req.json

# 3. 비동기 요청
JOB_ID=$(curl -s -X POST "$BASE_URL/run" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @req.json | jq -r '.id')

# 4. 결과 조회
curl -s "$BASE_URL/status/$JOB_ID" \
  -H "Authorization: Bearer $API_KEY"
```

## 성능 참고

| 항목 | 값 |
|---|---|
| Cold start (첫 요청) | ~60~130초 (모델 로딩) |
| **full** 모드 실행 시간 | ~3~7초 |
| **detect** 모드 실행 시간 | ~4~5초 |
| **ocr** 모드 실행 시간 | ~1~2초 |
| 지원 이미지 형식 | PNG, JPG, BMP 등 |
| 최대 이미지 크기 | RunPod 페이로드 제한 (10MB) |
| OCR 언어 | 한국어 + 영어 |

### 모드별 사용 모델

| 모드 | YOLOv8 | Florence-2 | PaddleOCR | 용도 |
|---|---|---|---|---|
| `full` | O | O | O | UI 요소 감지 + 캡션 + 텍스트 인식 |
| `detect` | O | O | X | UI 요소 감지 + 캡션만 |
| `ocr` | X | X | O | 텍스트 인식만 |
