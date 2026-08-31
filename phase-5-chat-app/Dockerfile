# Multi-stage build for the chat server. No torch — inference is NumPy — so the image stays
# small enough to fit the 0.5 GB Artifact Registry free tier. Build context is this folder:
#   gcloud builds submit phase-5-chat-app --tag $IMAGE
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY *.py ./
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
