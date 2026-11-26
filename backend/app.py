"""English <-> Sanskrit translation API for Hugging Face Spaces.

POST /translate  {text, source, target}  ->  {translation, romanized}
source/target: "en" or "sa"

Uses IndicTrans2 (distilled 200M) by default. To switch to your fine-tuned
model later, set the MODEL_EN_SA (and/or MODEL_SA_EN) variable in the Space
settings to its Hugging Face repo id.
"""
import os
import threading

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

try:
    from IndicTransToolkit.processor import IndicProcessor
except ImportError:  # older toolkit layout
    from IndicTransToolkit import IndicProcessor

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

MODELS = {
    ("en", "sa"): os.getenv("MODEL_EN_SA", "ai4bharat/indictrans2-en-indic-dist-200M"),
    ("sa", "en"): os.getenv("MODEL_SA_EN", "ai4bharat/indictrans2-indic-en-dist-200M"),
}
LANG_CODES = {"en": "eng_Latn", "sa": "san_Deva"}
HF_TOKEN = os.getenv("HF_TOKEN")  # needed if the model repo is gated
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "https://brandenleelundy-cpu.github.io"
    ).split(",")
    if o.strip()
]
MAX_CHARS = 5000
NUM_BEAMS = int(os.getenv("NUM_BEAMS", "4"))

torch.set_num_threads(max(1, os.cpu_count() or 1))

app = FastAPI(title="Sanskrit translation API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

processor = IndicProcessor(inference=True)
_loaded = {}
_lock = threading.Lock()


def get_model(direction):
    with _lock:
        if direction not in _loaded:
            name = MODELS[direction]
            tok = AutoTokenizer.from_pretrained(name, trust_remote_code=True, token=HF_TOKEN)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                name, trust_remote_code=True, token=HF_TOKEN
            ).eval()
            _loaded[direction] = (tok, model)
        return _loaded[direction]


def translate_lines(lines, src, tgt):
    tok, model = get_model((src, tgt))
    s, t = LANG_CODES[src], LANG_CODES[tgt]
    batch = processor.preprocess_batch(lines, src_lang=s, tgt_lang=t)
    inputs = tok(batch, truncation=True, padding="longest", return_tensors="pt",
                 return_attention_mask=True)
    with torch.inference_mode():
        out = model.generate(**inputs, use_cache=False, min_length=0,
                             max_length=256, num_beams=NUM_BEAMS, num_return_sequences=1)
    decoded = tok.batch_decode(out, skip_special_tokens=True,
                               clean_up_tokenization_spaces=True)
    return processor.postprocess_batch(decoded, lang=t)


class TranslateRequest(BaseModel):
    text: str = Field(..., max_length=MAX_CHARS)
    source: str = "en"
    target: str = "sa"


@app.get("/")
def health():
    return {"status": "ok", "models": {f"{a}-{b}": m for (a, b), m in MODELS.items()},
            "loaded": [f"{a}-{b}" for (a, b) in _loaded]}


@app.post("/translate")
def translate(req: TranslateRequest):
    direction = (req.source, req.target)
    if req.source == req.target:
        return {"translation": req.text, "romanized": ""}
    if direction not in MODELS:
        raise HTTPException(400, "Supported directions: en->sa, sa->en")

    lines = req.text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()]
    results = [""] * len(lines)
    if idx:
        try:
            translated = translate_lines([lines[i].strip() for i in idx], *direction)
        except OSError as e:  # model download failed (gated repo, missing HF_TOKEN, typo)
            raise HTTPException(503, f"Model could not be loaded: {e}".splitlines()[0][:300])
        except Exception as e:
            raise HTTPException(500, f"{type(e).__name__}: {e}"[:300])
        for i, tr in zip(idx, translated):
            results[i] = tr
    translation = "\n".join(results)

    romanized = ""
    if req.target == "sa":
        romanized = transliterate(translation, sanscript.DEVANAGARI, sanscript.IAST)
    return {"translation": translation, "romanized": romanized}


@app.on_event("startup")
def warm_up():
    # Load English->Sanskrit at boot so the first request isn't slow.
    threading.Thread(target=get_model, args=(("en", "sa"),), daemon=True).start()
