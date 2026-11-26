// Leave API_URL empty to use the built-in mock phrasebook.
// The backend must expose POST /translate {text, source, target} -> {translation, romanized}
// and allow CORS from https://<your-username>.github.io
window.APP_CONFIG = {
  API_URL: "https://bll1984-aqueous-api.hf.space",

  // Google AdSense. Leave empty for no ads.
  // ADSENSE_CLIENT: your publisher ID, e.g. "ca-pub-1234567890123456"
  // ADSENSE_SLOT:   an ad unit ID (Ads → By ad unit → Display ads), e.g. "1234567890".
  //                 Leave it empty to let AdSense "Auto ads" choose where ads go.
  ADSENSE_CLIENT: "",
  ADSENSE_SLOT: ""
};
