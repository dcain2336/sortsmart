# SortSmart Business Advisor

**AMD Developer Hackathon: ACT III — Reinvent Commerce track**

An AI advisor that helps businesses cut waste costs and prove sustainability ROI —
with every dollar figure grounded in a verified rule engine, and the LLM layer
designed to run on **AMD infrastructure**.

## The idea

Retailers, restaurants, and shippers make packaging and waste decisions every day
with no data. SortSmart Business Advisor changes that: ask a plain-English question,
get a dollar-quantified answer.

> "We ship 2,000 packages a month in plastic mailers — what should we switch to?"
> → *"Bottom line: switching to padded paper mailers saves ~$1,200/yr and makes
> every package curbside-recyclable..."*

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Demo UI    │────▶│   REST API       │────▶│  BusinessAdvisor│
│  (ui/)      │     │   (api/server.py)│     │  (agent)        │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                     │
                              ┌──────────────────────┼──────────────────┐
                              ▼                      ▼                  ▼
                     ┌─────────────────┐   ┌─────────────────┐ ┌──────────────┐
                     │ sortsmart/      │   │sortsmart_biz    │ │ sortsmart_llm│
                     │ rule engine     │   │ cost models,    │ │ OpenAI-compat│
                     │ (vendored)      │   │ scoring, ROI    │ │ client       │
                     └─────────────────┘   └─────────────────┘ └──────────────┘
```

**Key design principle:** the LLM never invents numbers. The deterministic layer
(cost models + rule engine) computes every figure; the LLM synthesizes them into
advice. All cost figures are US national averages, clearly labeled as estimates.

## The AMD angle

The LLM client (`sortsmart_llm/client.py`) speaks the OpenAI-compatible
`/v1/chat/completions` API and is configured entirely by environment variables:

| Env var | Testing now | AMD Developer Cloud |
|---|---|---|
| `LLM_BASE_URL` | `https://tokenharbor.ai/v1` | `http://<gpu-instance>:8000/v1` |
| `LLM_MODEL` | `deepseek-v4.1-flash:free` | `meta-llama/Llama-3.1-8B-Instruct` |
| `LLM_API_KEY` | `<key>` | not needed (vLLM default) |

Swapping to AMD-hosted inference is a **config change only** — zero code changes.
See [`amd/`](amd/) for the full ROCm + vLLM deployment guide.

This satisfies the ACT III requirement that a meaningful part of the workload run
on AMD infrastructure: the LLM is the product's core intelligence — every answer
is synthesized by the model — and it runs on AMD Developer Cloud (Instinct GPUs
via ROCm, served with vLLM).

## Quick start

```bash
# 1. Configure the LLM backend (or use LLM_MOCK=true for offline testing)
export LLM_BASE_URL="https://tokenharbor.ai/v1"
export LLM_API_KEY="your-key"
export LLM_MODEL="deepseek-v4.1-flash:free"

# 2. Run the server
python3 api/server.py
# → http://127.0.0.1:8080/

# 3. Run the tests
python3 -m pytest tests/ -q
```

No dependencies beyond the Python standard library.

## Project layout

| Path | What |
|---|---|
| `sortsmart/` | Vendored SortSmart rule engine (advisor, knowledge base, tracker) |
| `sortsmart_business/` | Cost models, sustainability scoring (0-100), ROI recommendations |
| `sortsmart_llm/` | Model-agnostic LLM client, prompts, advisor agent |
| `api/server.py` | REST API + static UI server (stdlib only) |
| `ui/index.html` | Demo web interface |
| `amd/` | AMD Developer Cloud / ROCm deployment guide |
| `tests/` | Unit tests (14, all passing, no LLM needed) |

## API

- `GET /api/health` — backend status + model info
- `POST /api/ask` — `{"question", "business_type"?, "monthly_shipments"?, "packaging"?}` → answer + grounded figures
- `POST /api/brief` — business profile → full cost/score/recommendation brief

## License

MIT — see [LICENSE](LICENSE).
