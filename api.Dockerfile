FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -g 1000 provstor && \
    useradd -u 1000 -g provstor provstor

COPY --chown=provstor:provstor src/provstor_api ./provstor_api

ENV PYTHONPATH=/app
ENV USER=provstor

EXPOSE 8000
CMD ["python3", "provstor_api/main.py"]
