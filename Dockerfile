FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
COPY fieldbio ./fieldbio
COPY content ./content
COPY vapi ./vapi

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn fieldbio.app:app --host 0.0.0.0 --port ${PORT:-8080}"]

