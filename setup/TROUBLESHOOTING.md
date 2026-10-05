# Troubleshooting

- **`ollama: command not found`**: restart the terminal after installation.
- **macOS app copied but not started**: run `open /Applications/Ollama.app`.
- **model missing**: run `ollama pull qwen3:4b-instruct` and
  `ollama pull nomic-embed-text`.
- **Python package missing**: run `python -m pip install -r requirements.txt`.
- **readiness checker fails**: fix that issue before running workshop stages.
- **agent output varies**: expected; the LLM is probabilistic. The guardrails
  and controlled outcome should remain authoritative.
