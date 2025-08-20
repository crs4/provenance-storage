FROM python:3.13-slim

WORKDIR /app

COPY src/provstor_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/provstor_api ./provstor_api

ENV PYTHONPATH=/app

RUN touch provstor_api/__init__.py
RUN touch provstor_api/routes/__init__.py
RUN touch provstor_api/utils/__init__.py

ARG API_PORT=8000
EXPOSE ${API_PORT}
CMD ["python3", "provstor_api/main.py"]
