# SortSmart Business Advisor — Submission Writeup
## AMD Developer Hackathon: ACT III — Reinvent Commerce track
## Team ArcOmega

---

## Short description (paste into lablab.ai)

SortSmart Business Advisor is an AI advisor that helps retailers, restaurants, and shippers cut packaging and waste costs — ask a plain-English question, get a dollar-quantified answer. A deterministic rule engine grounds every figure in verified cost data; an LLM layer running on AMD infrastructure turns those figures into conversational advice.

---

## Long description (paste into lablab.ai)

### Inspiration

Every day, small and mid-size businesses make packaging and waste decisions with no data: which mailer to buy, whether composting pays off, what their waste actually costs. Sustainability consultants charge thousands for audits most businesses will never buy. Meanwhile, packaging is often a business's most visible environmental footprint — and a controllable cost line. We built SortSmart Business Advisor to put a sustainability analyst on every business owner's phone, for free.

### What it does

Ask a plain-English question and get a dollar-quantified answer:

> "We ship 2,000 packages a month in plastic mailers — what should we switch to?"
> → "Bottom line: switching to padded paper mailers saves ~$1,200/yr and makes every package curbside-recyclable."

The app also produces full business briefs: a 0–100 sustainability score with a transparent point-by-point breakdown, current waste cost estimates, and ranked recommendations with projected annual savings. Every number is traceable to its source — the LLM never invents figures.

### How we built it

Three layers, each doing what it does best:

1. **Deterministic rule engine** (`sortsmart/`) — vendored from the original SortSmart project: waste-stream knowledge base, sorting advisor, tracking.
2. **Business intelligence layer** (`sortsmart_business/`) — cost models built on US national averages (EPA data, Waste Business Journal tipping-fee surveys): per-ton disposal costs, per-unit packaging comparisons, business archetype profiles, a 0–100 sustainability scoring system, and ROI-ranked recommendations.
3. **LLM advisor layer** (`sortsmart_llm/`) — a model-agnostic client speaking the OpenAI-compatible `/v1/chat/completions` API. It receives grounded figures from the deterministic layer and synthesizes them into conversational advice. Key design principle: the LLM is a narrator, not a calculator — every dollar figure comes from the verified cost models.

The whole backend is Python with zero third-party dependencies (standard library only); the UI is a single self-contained HTML file.

### The AMD angle

The LLM is the product's core intelligence — every answer is synthesized by the model — and it is built to run on AMD infrastructure. The client is configured entirely by environment variables, so moving from our test backend to an AMD-hosted model is a config change only, zero code changes:

| | Testing | AMD Developer Cloud |
|---|---|---|
| `LLM_BASE_URL` | `https://tokenharbor.ai/v1` | `http://<gpu-instance>:8000/v1` |
| `LLM_MODEL` | `deepseek-v4.1-flash:free` | `meta-llama/Llama-3.1-8B-Instruct` |

On AMD Developer Cloud, the model is served with vLLM on ROCm-ready Instinct GPUs — vLLM exposes the same OpenAI-compatible API, so the swap is seamless. Full deployment guide in `amd/`. This satisfies the ACT III requirement: a meaningful part of the workload (the conversational intelligence at the heart of the product) runs on AMD infrastructure.

### Business value

- **Direct cost savings:** packaging switches identified by the advisor typically save $1,000–$5,000/yr for a mid-size shipper; waste-stream re-routing (landfill → recycle/compost) cuts per-ton disposal costs nearly in half ($57/ton landfill vs $35 recycle / $30 compost, US averages).
- **Sustainability proof:** the 0–100 score gives businesses a credible, explainable metric for marketing, ESG reporting, and customer trust — without a $10k consultant audit.
- **Market:** 30M+ US small businesses; packaging decisions are made daily with zero tooling today.

### What's next

Merchant integrations (Shopify/WooCommerce packaging data), pooled multi-location benchmarking, and learned per-business waste profiles that improve recommendations over time.

---

## Technology tags (paste into lablab.ai — up to 25)

python, llm, openai-api, vllm, rocm, amd, amd-developer-cloud, rest-api, sustainability, fintech, cost-optimization, retail-tech, conversational-ai, rule-engine, data-modeling, html, javascript, css, rest, json, open-source, mit-license, small-business, esg, roi

---

## Links

- GitHub: https://github.com/dcain2336/sortsmart
- Demo video: [YouTube URL — Scott to upload]
- Live demo: [URL — to be deployed]
- Team: ArcOmega — https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii/arcomega
