FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/provstor_api ./provstor_api

ENV PYTHONPATH=/app

ARG API_PORT=8000
EXPOSE ${API_PORT}
CMD ["python3", "provstor_api/main.py"]
