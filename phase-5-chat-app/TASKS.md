# Phase 5 — Tasks & Deliverables

Do everything in **Google Cloud Shell**. Read [README.md](README.md) first. You need your
Phase-2 public model URL, Phase-3 BigQuery table, and Phase-4 Firestore already in place.

Set these once per shell session:

```bash
export PROJECT=$(gcloud config get-value project)
export REGION=us-central1
export IMAGE=$REGION-docker.pkg.dev/$PROJECT/eurecomgpt/chat:v1
export MODEL_URL=https://storage.googleapis.com/$PROJECT-eurecomgpt/model.safetensors  # Phase 2
export BQ_TABLE=$PROJECT.eurecomgpt.tfidf                                               # Phase 3
export BUCKET=$PROJECT-eurecomgpt
```

---

## Task 1 — Enable the APIs

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
    cloudbuild.googleapis.com bigquery.googleapis.com firestore.googleapis.com
```

---

## Task 2 — Implement the RAG helpers and run the unit tests

Fill the TODOs in [rag.py](rag.py) — `rank_topk` and `build_rag_prompt`. Then, offline:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest phase-5-chat-app/tests/test_units.py -p autograder.points -q
```

---

## Task 3 — Build the chat image and push it

```bash
gcloud builds submit phase-5-chat-app --tag $IMAGE
```

---

## Task 4 — Deploy to Cloud Run + grant data access

```bash
gcloud run deploy chat --image=$IMAGE --region=$REGION --allow-unauthenticated \
    --min-instances=0 --port=8080 --memory=1Gi \
    --set-env-vars=MODEL_URL=$MODEL_URL,BQ_TABLE=$BQ_TABLE

# let the Cloud Run service account read BigQuery + write Firestore
CR_SA=$(gcloud run services describe chat --region=$REGION \
    --format='value(spec.template.spec.serviceAccountName)')
CR_SA=${CR_SA:-$(gcloud iam service-accounts list --filter=compute --format='value(email)')}
for ROLE in roles/bigquery.jobUser roles/bigquery.dataViewer roles/datastore.user; do
  gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$CR_SA" --role="$ROLE"
done

export CHAT_URL=$(gcloud run services describe chat --region=$REGION --format='value(status.url)')
echo $CHAT_URL
curl -s -X POST $CHAT_URL/chat -H 'Content-Type: application/json' \
     -d '{"session_id":"cli","message":"love and the king"}'
```

---

## Task 5 — Host the chat UI on Cloud Storage

```bash
gcloud storage cp phase-5-chat-app/ui/index.html gs://$BUCKET/index.html
export UI_URL=https://storage.googleapis.com/$BUCKET/index.html
echo $UI_URL
```

Open `$UI_URL`, paste your `$CHAT_URL` into the field, and chat. (The bucket is already public
from Phases 2–3.)

---

## Task 6 — Generate the report

```bash
python phase-5-chat-app/make_report.py --chat-url $CHAT_URL --ui-url $UI_URL
```

This chats a few times and reads Firestore back to prove the turns were stored, writing
`submission/phase5_report.json`.

---

## Task 7 — Commit, push, confirm green CI

Commit `rag.py` and `submission/phase5_report.json`, then push. The **`autograde-phase-5`**
workflow runs the offline tests + live-curls your chat server.

---

## Task 8 — Tear down (after you're graded)

```bash
gcloud run services delete chat --region=$REGION --quiet
```

## Deliverables

1. Filled `rag.py`.
2. A deployed, public **Cloud Run** chat server + the **chat UI** on Cloud Storage.
3. `submission/phase5_report.json`.
4. A **green** `autograde-phase-5` CI run + a 90-second demo recording.

## Grading rubric (100 pts)

| Check | Points | Where |
|---|---:|---|
| `rank_topk` ranks by summed tfidf | 15 | public unit test |
| `rank_topk` returns exactly k | 10 | public unit test |
| `build_rag_prompt` assembles context + query | 15 | public unit test |
| `/healthz` returns 200 | 10 | public (live-curl) |
| `/chat` returns a reply + retrieved docs | 25 | public (live-curl) |
| chat + UI URLs recorded | 8 | public (report) |
| turns stored in Firestore (counter = 2× chats) | 7 | public (report) |
| chat_url is a real Cloud Run URL | 6 | **hidden** |
| sample reply + retrieved context recorded | 4 | **hidden** |
| **Total** | **100** | |

Public checks (80 pts) you can verify yourself after deploying + `make_report.py`; while
coding, just use `tests/test_units.py`.
