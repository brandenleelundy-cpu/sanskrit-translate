"""English / Hindi / Sanskrit translation API for Hugging Face Spaces.

POST /translate  {text, source, target}  ->  {translation, romanized}
source/target: "en", "hi" or "sa"

Uses IndicTrans2 (distilled 200M) by default. To switch English->Sanskrit to
your fine-tuned model, set the MODEL_EN_SA variable in the Space settings to
its Hugging Face repo id; English->Hindi keeps using MODEL_EN_INDIC.
Hindi <-> Sanskrit goes through English.
"""
import os
import threading
import time

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

EN_INDIC = os.getenv("MODEL_EN_INDIC", "ai4bharat/indictrans2-en-indic-dist-200M")
INDIC_EN = os.getenv("MODEL_INDIC_EN", os.getenv("MODEL_SA_EN", "ai4bharat/indictrans2-indic-en-dist-200M"))
MODELS = {  # direction -> model repo; directions sharing a repo share one loaded copy
    ("en", "sa"): os.getenv("MODEL_EN_SA", EN_INDIC),
    ("en", "hi"): EN_INDIC,
    ("sa", "en"): INDIC_EN,
    ("hi", "en"): INDIC_EN,
}
LANG_CODES = {"en": "eng_Latn", "hi": "hin_Deva", "sa": "san_Deva"}
HF_TOKEN = os.getenv("HF_TOKEN")  # needed if the model repo is gated
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "https://brandenleelundy-cpu.github.io"
    ).split(",")
    if o.strip()
]
MAX_CHARS = 5000
NUM_BEAMS = int(os.getenv("NUM_BEAMS", "3"))

# Free Spaces get 2 vCPUs, but os.cpu_count() reports the whole host machine,
# which oversubscribes PyTorch and makes generation crawl.
torch.set_num_threads(int(os.getenv("TORCH_THREADS", "2")))
torch.set_num_interop_threads(1)

app = FastAPI(title="English / Hindi / Sanskrit translation API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

processor = IndicProcessor(inference=True)
_loaded = {}
_lock = threading.Lock()
_gen_lock = threading.Lock()  # one generation at a time on a small CPU


def get_model(direction):
    name = MODELS[direction]
    with _lock:
        if name not in _loaded:
            tok = AutoTokenizer.from_pretrained(name, trust_remote_code=True, token=HF_TOKEN)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                name, trust_remote_code=True, token=HF_TOKEN
            ).eval()
            _loaded[name] = (tok, model)
        return _loaded[name]


def translate_lines(lines, src, tgt):
    tok, model = get_model((src, tgt))
    s, t = LANG_CODES[src], LANG_CODES[tgt]
    batch = processor.preprocess_batch(lines, src_lang=s, tgt_lang=t)
    inputs = tok(batch, truncation=True, padding="longest", return_tensors="pt",
                 return_attention_mask=True)
    with _gen_lock, torch.inference_mode():
        out = model.generate(**inputs, use_cache=False, min_length=0,
                             max_length=256, num_beams=NUM_BEAMS, num_return_sequences=1)
    decoded = tok.batch_decode(out, skip_special_tokens=True,
                               clean_up_tokenization_spaces=True)
    return processor.postprocess_batch(decoded, lang=t)


def translate_any(lines, src, tgt):
    if (src, tgt) in MODELS:
        return translate_lines(lines, src, tgt)
    # Hindi <-> Sanskrit: pivot through English
    return translate_lines(translate_lines(lines, src, "en"), "en", tgt)


class TranslateRequest(BaseModel):
    text: str = Field(..., max_length=MAX_CHARS)
    source: str = "en"
    target: str = "sa"


@app.get("/")
def health():
    return {"status": "ok", "languages": list(LANG_CODES),
            "models": {f"{a}-{b}": m for (a, b), m in MODELS.items()},
            "loaded": list(_loaded)}


@app.post("/translate")
def translate(req: TranslateRequest):
    direction = (req.source, req.target)
    if req.source not in LANG_CODES or req.target not in LANG_CODES:
        raise HTTPException(400, f"Supported languages: {', '.join(LANG_CODES)}")
    if req.source == req.target:
        return {"translation": req.text, "romanized": ""}

    t0 = time.time()
    lines = req.text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()]
    results = [""] * len(lines)
    if idx:
        try:
            translated = translate_any([lines[i].strip() for i in idx], *direction)
        except OSError as e:  # model download failed (gated repo, missing HF_TOKEN, typo)
            raise HTTPException(503, f"Model could not be loaded: {e}".splitlines()[0][:300])
        except Exception as e:
            raise HTTPException(500, f"{type(e).__name__}: {e}"[:300])
        for i, tr in zip(idx, translated):
            results[i] = tr
    translation = "\n".join(results)

    romanized = ""
    if req.target in ("sa", "hi"):
        romanized = transliterate(translation, sanscript.DEVANAGARI, sanscript.IAST)
    return {"translation": translation, "romanized": romanized,
            "seconds": round(time.time() - t0, 2)}


@app.on_event("startup")
def warm_up():
    # Load English->Sanskrit at boot so the first request isn't slow.
    threading.Thread(target=get_model, args=(("en", "sa"),), daemon=True).start()
