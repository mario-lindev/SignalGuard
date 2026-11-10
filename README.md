# SignalGuard

Listen today. Keep water flowing.

A runnable research prototype for community pump monitoring using phone audio and per-pump acoustic anomaly detection. Record a check, build a verified healthy baseline, compare later recordings, review history and export results.

## Run

Requires Python 3.9 or newer. No package installation or API keys needed.

```sh
python3 signalguard.py
```

Open http://localhost:8000. Add a pump, save at least five separate verified healthy recordings, then uncheck the baseline option to compare a new recording. A healthy baseline must be confirmed independently; the model does not establish that a pump is healthy.

Phone microphone recording requires HTTPS (localhost is allowed on the host computer). For a trusted local network, serve behind an HTTPS reverse proxy; `HOST=0.0.0.0 python3 signalguard.py` enables LAN binding but does not add TLS or authentication. Keep this development server off the public internet. Alternatively transfer a phone recording and upload it from the host browser.

## Included

- Responsive browser UI with 10-second microphone capture and audio upload.
- Browser decoding into 16-bit PCM WAV; Python analysis of 3–30-second mono/stereo audio.
- Silence and clipping checks, pump-specific Gaussian baseline learning and deviation scores.
- SQLite persistence, listening history and CSV export. No raw audio retained.
- Research review, collection protocol, evaluation plan and explicit limitations.
- Standard-library tests and GitHub Actions CI.

## Model and limitations

This is a statistical machine-learning baseline trained by your healthy recordings, not a pretrained fault classifier. With no baseline it returns **Uncalibrated**. Scores measure sound deviation, not failure probability. Thresholds are provisional. It cannot diagnose damage, predict a failure date, or establish water safety. It has not been benchmarked or field-validated. Industrial acoustic research supports investigating this approach but does not prove phone-based rural-pump reliability.

See [research and validation plan](docs/RESEARCH.md) for primary sources, feature details, domain-shift risks and next steps. No dataset or fabricated performance claims are bundled.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Tests use generated tones to check pipeline mechanics only; they do not measure real fault-detection accuracy.

## Layout

`signalguard.py`: HTTP API, audio features, learned model, SQLite. `static/`: accessible browser client. `docs/RESEARCH.md`: evidence and field plan. `tests/`: analysis and API tests.

Runtime data is written to `data/signalguard.db` and excluded from Git. API: `GET /api/pumps`, `POST /api/pumps` (JSON name/location), `POST /api/analyze` (WAV body, X-Pump-Id and X-Baseline headers). Maximum request size is 6 MB. This single-user prototype has no accounts or authorization.
