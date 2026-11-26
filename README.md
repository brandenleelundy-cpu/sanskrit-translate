# English → Sanskrit Translator

Static frontend for the translation site, deployed with GitHub Pages.
Until the fine-tuned IndicTrans2 backend is live, it runs on a small mock phrasebook.

## Publish on GitHub Pages

1. Create an empty repo on GitHub, e.g. `sanskrit-translate`.
2. Push this folder:
   ```bash
   git remote add origin https://github.com/<you>/sanskrit-translate.git
   git push -u origin main
   ```
3. In the repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. The workflow in `.github/workflows/pages.yml` deploys on every push to `main`.
   The site appears at `https://<you>.github.io/sanskrit-translate/`.

## Connect the real model

GitHub Pages only serves static files, so the model runs on a free Hugging Face
Space. The backend lives in [`backend/`](backend/).

1. On huggingface.co: **New → Space**, SDK **Docker** (blank template), hardware **CPU basic (free)**, public.
2. **Files → Add file → Upload files**: drop in the four files from `backend/`
   (`app.py`, `Dockerfile`, `requirements.txt`, `README.md`) and commit.
3. If the build log says the model is gated: accept the terms on the model's page
   and add an `HF_TOKEN` secret (a read token) in the Space's settings.
4. When the Space shows *Running*, set `API_URL` in `config.js` to
   `https://<hf-username>-<space-name>.hf.space` and push.

Free Spaces sleep after a period of no traffic; the first request afterwards takes a minute or two.

The backend contract:

```
POST /translate
{ "text": "Where is the train station?", "source": "en", "target": "sa" }
→ { "translation": "…", "romanized": "…" }
```

It must allow CORS from `https://<you>.github.io`. If the backend fails, the page falls back to the mock.
