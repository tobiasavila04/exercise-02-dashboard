FROM python:3.9-slim as builder
 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
 
WORKDIR /install
 
COPY requirements.txt .
 
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt
 
FROM python:3.9-slim
 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
 
WORKDIR /app
 
COPY --from=builder /install /usr/local
 
RUN useradd -m appuser
USER appuser
 
COPY app.py .
 
EXPOSE 8501
 
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/')" || exit 1
 
CMD ["python", "app.py"]
 