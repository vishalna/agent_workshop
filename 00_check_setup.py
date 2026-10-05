"""Pre-workshop readiness check.

Validates the local runtime, both Ollama models, generation, embeddings, and
native tool calling before a participant starts the exercises.
"""

import shutil
import subprocess
import sys
import ollama

CHAT_MODEL = "qwen3:4b-instruct"
EMBED_MODEL = "nomic-embed-text"

print("\n=== WORKSHOP READINESS CHECK ===")

if sys.version_info < (3, 10):
    raise SystemExit("✗ Python 3.10+ required")
print(f"✓ Python {sys.version.split()[0]}")

if not shutil.which("ollama"):
    raise SystemExit("✗ Ollama CLI not found")
print("✓ Ollama installed")

print("✓ Python ollama package installed")

subprocess.run(
    ["ollama", "list"],
    check=True,
    stdout=subprocess.DEVNULL,
    timeout=15,
)
print("✓ Ollama service reachable")

models = ollama.list()
names = {m.model for m in models.models}
for required in (CHAT_MODEL, EMBED_MODEL):
    if required not in names and f"{required}:latest" not in names:
        raise SystemExit(f"✗ Missing model: {required}")
print(f"✓ Chat model installed: {CHAT_MODEL}")
print(f"✓ Embedding model installed: {EMBED_MODEL}")

reply = ollama.chat(
    model=CHAT_MODEL,
    messages=[{"role": "user", "content": "Reply only LOCAL_LLM_OK"}],
)
if "LOCAL_LLM_OK" not in reply.message.content:
    raise SystemExit("✗ Local LLM response check failed")
print("✓ Local LLM responding")

embedding = ollama.embed(model=EMBED_MODEL, input="refund policy")
if not embedding["embeddings"] or not embedding["embeddings"][0]:
    raise SystemExit("✗ Embedding check failed")
print("✓ Local embeddings responding")


def workshop_ping(case_id: str):
    """Return a test acknowledgement for a case ID."""
    return {"case_id": case_id, "ok": True}


tool_reply = ollama.chat(
    model=CHAT_MODEL,
    messages=[
        {
            "role": "user",
            "content": "Use workshop_ping for case TEST-1. Do not answer directly.",
        }
    ],
    tools=[workshop_ping],
)

if not tool_reply.message.tool_calls:
    raise SystemExit("✗ Tool-calling check failed")
print("✓ Tool calling supported")

print("\n🎉 READY FOR WORKSHOP")
print("Next: python 01_llm_only/run.py")
