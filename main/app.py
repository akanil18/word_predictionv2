from __future__ import annotations

import os
import re
import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# TensorFlow logs are noisy; this keeps the console readable.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences


BASE_DIR = Path(__file__).resolve().parent
# Artifacts are stored at repo_root/model/* by default.
REPO_ROOT = BASE_DIR.parent
MODEL_DIR = REPO_ROOT / "model"
MODEL_PATH = MODEL_DIR / "model.h5"
TOKENIZER_PATH = MODEL_DIR / "tokenizer.pkl"


def _clean_text(s: str) -> str:
    # Must match training-time cleaning as closely as possible.
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-zA-Z\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _infer_max_len_from_model(keras_model) -> int:
    # Training used max_len-1 as input length.
    # For common Sequential models, input_shape is (None, timesteps).
    input_shape = getattr(keras_model, "input_shape", None)
    if not input_shape or len(input_shape) < 2 or input_shape[1] is None:
        raise RuntimeError(
            "Unable to infer sequence length from the model. "
            "Please provide MAX_LEN as an environment variable."
        )
    return int(input_shape[1]) + 1


def predict_next_word(text: str, keras_model, tokenizer, max_len: int) -> str:
    text = _clean_text(text)

    token_list = tokenizer.texts_to_sequences([text])[0]
    if len(token_list) == 0:
        return "[UNKNOWN]"

    token_list = pad_sequences([token_list], maxlen=max_len - 1, padding="pre")
    predictions = keras_model.predict(token_list, verbose=0)
    predicted_index = int(np.argmax(predictions, axis=-1)[0])

    return tokenizer.index_word.get(predicted_index, "[UNKNOWN]")


def predict_top_k(text: str, keras_model, tokenizer, max_len: int, k: int) -> List[str]:
    text = _clean_text(text)

    token_list = tokenizer.texts_to_sequences([text])[0]
    if len(token_list) == 0:
        return ["[UNKNOWN]"]

    token_list = pad_sequences([token_list], maxlen=max_len - 1, padding="pre")
    probs = keras_model.predict(token_list, verbose=0)[0]

    k = max(1, int(k))
    # argsort descending
    top_idx = np.argsort(probs)[::-1][:k]

    words: List[str] = []
    for idx in top_idx:
        w = tokenizer.index_word.get(int(idx))
        if w:
            words.append(w)
    return words or ["[UNKNOWN]"]


class PredictRequest(BaseModel):
    text: str = Field(..., description="Input text/prefix")
    k: int = Field(1, ge=1, le=20, description="Number of suggestions")


class PredictResponse(BaseModel):
    input: str
    next_word: str
    suggestions: List[str]


app = FastAPI(title="Next Word Prediction API")

# Allow opening the frontend directly from file:// or any local dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _load_artifacts() -> None:
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Missing model file: {MODEL_PATH}")
    if not TOKENIZER_PATH.exists():
        raise RuntimeError(f"Missing tokenizer file: {TOKENIZER_PATH}")

    app.state.model = load_model(str(MODEL_PATH))
    with open(TOKENIZER_PATH, "rb") as f:
        app.state.tokenizer = pickle.load(f)

    # Prefer MAX_LEN explicitly, else infer from the model.
    env_max_len = os.getenv("MAX_LEN")
    if env_max_len:
        app.state.max_len = int(env_max_len)
    else:
        app.state.max_len = _infer_max_len_from_model(app.state.model)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    print(f"Received prediction request: text='{req.text}', k={req.k}")
    model = app.state.model
    tokenizer = app.state.tokenizer
    max_len = app.state.max_len

    suggestions = predict_top_k(req.text, model, tokenizer, max_len, req.k)
    next_word = suggestions[0] if suggestions else "[UNKNOWN]"

    return PredictResponse(input=req.text, next_word=next_word, suggestions=suggestions)
