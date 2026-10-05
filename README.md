# Production-Ready Refund Agent Workshop

This is a **local-first teaching package**. It uses Ollama so participants do
not need API keys, cloud credits, Docker, databases, or a running web server.

## Learning path

1. **LLM only** — plausible language is not a grounded decision.
2. **Trusted tools** — connect the model to systems of record.
3. **Semantic RAG** — retrieve policy with local embeddings.
4. **Guardrails** — let the LLM interpret language; let code enforce hard rules.
5. **Guarded agent loop** — let the model choose tools, but supervise identity,
   sequencing, consequential actions, stop rules, and final claims.
6. **Evals** — test deterministic controls against golden cases.

## Models

- Generation/tool use: `qwen3:4b-instruct`
- Embeddings: `nomic-embed-text`

## First run

```bash
python -m pip install -r requirements.txt
python 00_check_setup.py
```

Do not begin the live workshop until the checker prints `READY FOR WORKSHOP`.

Then run:

```bash
python 01_llm_only/run.py
python 02_tools/run.py
python 03_rag/run.py
python 04_guardrails/run.py
python 05_agent_loop/run.py
python 06_evals/run_evals.py
```

## Important

This package is a workshop simulation. It does **not** move real money or call
a real order/refund service. Production deployment additionally needs
authentication/authorization, idempotent write APIs, secrets management,
observability, rate/latency controls, PII controls, durable audit trails,
human-review workflow, rollout controls, and organization-specific policy.
