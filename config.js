// Leave API_URL empty to use the built-in mock phrasebook.
// Set it to your model backend (e.g. a Hugging Face Space) once it's running:
//   API_URL: "https://your-name-sanskrit-api.hf.space"
// The backend must expose POST /translate {text, source, target} -> {translation, romanized}
// and allow CORS from https://<your-username>.github.io
window.APP_CONFIG = {
  API_URL: ""
};
