# Real-Time Voice AI

Production-oriented streaming voice pipeline:

Microphone -> Silero VAD -> Soniox Streaming STT -> Gemini Streaming LLM -> Soniox Streaming TTS -> Speaker

## Current implementation

- 16-kHz mono PCM16 capture
- Silero VAD
- Soniox realtime STT
- Gemini streaming text generation
- Soniox realtime TTS
- conversation state
- latency instrumentation
- benchmark scaffolding
- provider isolation

## Setup

Ubuntu:

```bash
sudo apt update
sudo apt install -y portaudio19-dev python3-dev
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/.env.example config/.env
```

Fill in `SONIOX_API_KEY` and `GOOGLE_API_KEY`.

Run:

```bash
python -m app.main
```

List audio devices:

```bash
python scripts/check_microphone.py
```

Run tests:

```bash
pytest
```

## Important

The Gemini Live native-audio branch is intentionally isolated from the cascaded
pipeline and should be implemented only after the cascaded pipeline is validated.
