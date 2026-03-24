FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# OmniParser v2 클론 (master)
RUN git clone --depth 1 https://github.com/microsoft/OmniParser.git /app/OmniParser

# OmniParser utils.py 패치 - filtered_boxes가 list of list일 경우 대응
RUN sed -i "s/filtered_boxes_elem = sorted(filtered_boxes, key=lambda x: x\['content'\] is None)/filtered_boxes_elem = sorted(filtered_boxes, key=lambda x: x['content'] is None if isinstance(x, dict) else True)/" /app/OmniParser/util/utils.py

# Python 의존성 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# OmniParser 자체 의존성 중 누락분 설치
RUN pip install --no-cache-dir easyocr

# 모델 가중치 다운로드 (OmniParser v2)
RUN pip install --no-cache-dir "huggingface_hub>=0.23.2,<1.0" && \
    python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('microsoft/OmniParser-v2.0', \
    allow_patterns=['icon_detect/*', 'icon_caption/*'], \
    local_dir='/app/OmniParser/weights')" && \
    mv /app/OmniParser/weights/icon_caption /app/OmniParser/weights/icon_caption_florence

# PaddleOCR 한국어 모델 사전 다운로드 (cold start 시간 단축)
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='korean', use_angle_cls=False, use_gpu=False, show_log=False)"

# 핸들러 복사
COPY handler.py /app/handler.py

CMD ["python", "-u", "/app/handler.py"]
