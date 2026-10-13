# AMD Deployment — SortSmart Business Advisor

The LLM layer is **model-agnostic**: it talks to any OpenAI-compatible
`/v1/chat/completions` endpoint. Moving from the current test backend to an
AMD-hosted model is a **config change only** — no code changes.

## Current (testing)

```
LLM_BASE_URL=https://tokenharbor.ai/v1
LLM_API_KEY=<key>
LLM_MODEL=deepseek-v4.1-flash:free
```

## Target (AMD Developer Cloud)

Once AMD Developer Cloud credits are approved:

1. Spin up a GPU instance on AMD Developer Cloud (ROCm-ready images available).
2. Serve an open model with vLLM (ROCm-compatible):
   ```bash
   # on the AMD Developer Cloud GPU instance
   pip install vllm
   vllm serve meta-llama/Llama-3.1-8B-Instruct \
     --host 0.0.0.0 --port 8000
   ```
   vLLM exposes an OpenAI-compatible API at `/v1` out of the box.
3. Point the advisor at it — config only:
   ```
   LLM_BASE_URL=http://<instance-ip>:8000/v1
   LLM_API_KEY=not-needed          # vLLM default needs no key
   LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
   ```
4. Restart the API server. Done — the advisor now runs its LLM workload
   on AMD infrastructure, satisfying the ACT III tech requirement.

## Why this satisfies the contest requirement

> "Every project must run a meaningful part of its workload on AMD
> infrastructure or AMD hardware."

The LLM is the core intelligence of the Business Advisor — every answer is
synthesized by the model from grounded business data. Hosting that model on
AMD Developer Cloud (Instinct GPUs via ROCm + vLLM) puts the product's
central workload on AMD infrastructure.

## Suggested models (ROCm + vLLM tested)

| Model | Params | Notes |
|---|---|---|
| Llama-3.1-8B-Instruct | 8B | Fast, strong instruction following |
| Qwen2.5-7B-Instruct | 7B | Strong multilingual, good reasoning |
| Mistral-7B-Instruct-v0.3 | 7B | Efficient, Apache-2.0 |

All run comfortably on a single AMD Developer Cloud GPU instance.

## Local ROCm testing (optional)

If you have AMD hardware locally:
```bash
# ROCm install: https://rocm.docs.amd.com/
pip install vllm  # ROCm wheels
vllm serve <model> --host 0.0.0.0 --port 8000
```
Then set `LLM_BASE_URL=http://localhost:8000/v1` as above.
