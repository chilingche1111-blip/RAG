FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.docker.txt .
RUN pip install --upgrade pip && pip install -r requirements.docker.txt

COPY app ./app
COPY data ./data
COPY scripts ./scripts
COPY docs ./docs
COPY README.md ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
