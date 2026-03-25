FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# 시스템 의존성 + 정리
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# OmniParser v2 클론 (최소한으로)
RUN git clone --depth 1 https://github.com/microsoft/OmniParser.git /app/OmniParser \
    && rm -rf /app/OmniParser/.git

# Python 의존성 설치 (torch/torchvision은 베이스 이미지에 포함)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# PaddleOCR 한국어 모델 사전 다운로드
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='korean', use_angle_cls=False, use_gpu=False, show_log=False)"

# 모델 가중치 다운로드 (OmniParser v2)
RUN pip install --no-cache-dir "huggingface_hub>=0.23.2,<1.0" && \
    python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('microsoft/OmniParser-v2.0', \
    allow_patterns=['icon_detect/*', 'icon_caption/*'], \
    local_dir='/app/OmniParser/weights')" && \
    mv /app/OmniParser/weights/icon_caption /app/OmniParser/weights/icon_caption_florence

# OmniParser utils.py 패치 (PaddleOCR 한국어 + easyocr 제거 + 기타)
COPY patch_utils.py /app/patch_utils.py
RUN python /app/patch_utils.py

# pip/huggingface 캐시 정리
RUN rm -rf /root/.cache/pip /root/.cache/huggingface /tmp/*

# 핸들러 복사
COPY handler.py /app/handler.py

CMD ["python", "-u", "/app/handler.py"]
