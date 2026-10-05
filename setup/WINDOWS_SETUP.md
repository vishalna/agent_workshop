# Windows setup

Open PowerShell and run:

```powershell
irm https://ollama.com/install.ps1 | iex
```

Close and reopen PowerShell if `ollama` is not immediately found. Then:

```powershell
ollama --version
ollama pull qwen3:4b-instruct
ollama pull nomic-embed-text
ollama list
python -m pip install -r requirements.txt
python 00_check_setup.py
```
