FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt ./server_requirements.txt
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt -r server_requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 7860

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]