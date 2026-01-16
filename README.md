# Next Word Prediction (FastAPI + Frontend)

This repo serves a trained next-word LSTM model via a FastAPI endpoint and includes a simple frontend to call it.

## What’s included

- `app.py` – FastAPI server that loads `model/model.h5` + `model/tokenizer.pkl` and exposes `/predict`
- `frontend/` – static HTML/CSS/JS UI that calls the API
- `requirements.txt` – Python dependencies

## API

### `POST /predict`

Request:

```json
{ "text": "deep learning is", "k": 5 }
```

Response:

```json
{
  "input": "deep learning is",
  "next_word": "...",
  "suggestions": ["...", "...", "..."]
}
```

### `GET /health`

Returns `{ "status": "ok" }`.

## Run

### Option A: run locally (no Docker)

1) Create/activate a Python environment (venv/conda).

2) Install dependencies.

3) Start the API using Uvicorn.

Depending on where the API file is located:
- If you have `main/app.py`: run `uvicorn main.app:app --reload`
- If you have `app.py` at the repo root: run `uvicorn app:app --reload`

4) Open `frontend/index.html` in your browser.

### Option B: run with Docker Compose

- Build and start: `docker compose up --build`
- Frontend: http://localhost:8080
- API: http://localhost:8000

Notes:
- If your model’s input length can’t be inferred, set `MAX_LEN` as an environment variable.
