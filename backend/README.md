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

English ↔ Sanskrit translation with IndicTrans2, for the site at
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
| `MODEL_SA_EN` | variable | Swap in a Sanskrit→English model |
| `ALLOWED_ORIGINS` | variable | Comma-separated sites allowed to call the API |
