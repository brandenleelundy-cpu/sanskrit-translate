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

GitHub Pages only serves static files, so the model backend has to run elsewhere
(Hugging Face Spaces, Render, a GPU VM, …). When it's up, set `API_URL` in `config.js`.

The backend contract:

```
POST /translate
{ "text": "Where is the train station?", "source": "en", "target": "sa" }
→ { "translation": "…", "romanized": "…" }
```

It must allow CORS from `https://<you>.github.io`. If the backend fails, the page falls back to the mock.
