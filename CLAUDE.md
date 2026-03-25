# RunPod - OmniParser v2

## 프로젝트 목적
RunPod에 OmniParser v2를 설치하고 운영하기 위한 모듈.

## 개요
- **OmniParser v2**: 화면 파싱 모델로, UI 요소를 인식하고 분석하는 데 사용
- **RunPod Serverless**: GPU 서버리스 엔드포인트로 배포 (Pod 아님)
- **OCR**: OmniParser 내장 PaddleOCR를 `lang="korean"` 으로 설정하여 한국어 + 영어 동시 인식
- **PaddleOCR 버전**: 2.9.1 (2.x 안정 버전 사용, 3.x는 PyTorch와 충돌)
- **PaddlePaddle 버전**: 2.6.2 (CPU, GPU 충돌 방지)

## RunPod API Key
```
rpa_G05IZNUHJPG3RPCPQQ2FQ4CYFHT752SWXSOWNFFK1kxcod
```

## Endpoint
- **Endpoint ID**: `v5j0gr4r45ga58`
- **API 모드**: `full` (전체), `detect` (UI감지만), `ocr` (OCR만)

## Docker 이미지 버전 관리
- **레지스트리**: `ghcr.io/kwonbyeongchun/omniparser-serverless`
- **버전 태그**: `1.0.{빌드번호}` (GitHub Actions run_number 사용)
- **push할 때마다 빌드번호가 자동으로 1씩 증가**
- 예: `1.0.25`, `1.0.26`, `1.0.27` ...
- `latest` 태그도 함께 push됨
- 메이저/마이너 버전 변경 시 `.github/workflows/build-push.yml`의 `VERSION_MAJOR`, `VERSION_MINOR` 수정

## GitHub 저장소
- **URL**: https://github.com/kwonbyeongchun/omniparser-runpod
- **계정**: kwonbyeongchun
