# The Phase-4 chat server, rebuilt with Firestore as its store. Same server.py, same rag.py
# (yours, from Phase 4), plus this phase's firestore_store.py (yours) and the Firestore client.
#
# The build context is the REPO ROOT, because the image needs files from two phase folders:
#   gcloud builds submit . --config=phase-5-firestore/cloudbuild.yaml --substitutions=_IMAGE=$IMAGE
FROM python:3.11-slim AS builder
WORKDIR /app
COPY phase-4-chat-app/requirements.txt ./req-chat.txt
COPY phase-5-firestore/requirements.txt ./req-firestore.txt
RUN pip install --no-cache-dir --prefix=/install -r req-chat.txt -r req-firestore.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY phase-4-chat-app/*.py ./
COPY phase-5-firestore/firestore_store.py ./
ENV PORT=8080
ENV STORE_BACKEND=firestore
EXPOSE 8080
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
