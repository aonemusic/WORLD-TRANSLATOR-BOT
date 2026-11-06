FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr tesseract-ocr-eng tesseract-ocr-mal tesseract-ocr-ara \
    tesseract-ocr-hin tesseract-ocr-urd tesseract-ocr-tam tesseract-ocr-spa \
    tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-chi-sim tesseract-ocr-jpn \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
RUN useradd --create-home --uid 10001 botuser && chown -R botuser:botuser /app
USER botuser
CMD ["python", "main.py"]
