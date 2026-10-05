# macOS setup

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

If the app was copied but did not start:

```bash
open /Applications/Ollama.app
```

Then:

```bash
ollama --version
ollama pull qwen3:4b-instruct
ollama pull nomic-embed-text
ollama list
python -m pip install -r requirements.txt
python 00_check_setup.py
```
