FROM python:3.9-slim
 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
 
WORKDIR /app
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY app.py .
 
EXPOSE 8501
 
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/')" || exit 1
 
CMD ["python", "app.py"]
 