---
title: Sanskrit Translate API
emoji: 📜
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# Sanskrit Translate API

English, Hindi and Sanskrit translation with IndicTrans2 (Hindi↔Sanskrit via English), for the site at
https://brandenleelundy-cpu.github.io/sanskrit-translate/

```
POST /translate
{ "text": "Where is the train station?", "source": "en", "target": "sa" }
→ { "translation": "…", "romanized": "…" }
```

Settings (Space → Settings → Variables and secrets):

| Name | Kind | Purpose |
|---|---|---|
| `HF_TOKEN` | secret | Read token, needed only if the model repo is gated |
| `MODEL_EN_SA` | variable | Swap in your fine-tuned English→Sanskrit model |
| `MODEL_EN_INDIC` | variable | English→Hindi model (default: IndicTrans2 en-indic 200M) |
| `MODEL_INDIC_EN` | variable | Hindi/Sanskrit→English model (default: IndicTrans2 indic-en 200M) |
| `ALLOWED_ORIGINS` | variable | Comma-separated sites allowed to call the API |
