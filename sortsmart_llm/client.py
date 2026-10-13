"""Model-agnostic LLM client (OpenAI-compatible chat completions API).

Configuration via environment variables — no code changes needed to swap models:
    LLM_BASE_URL  e.g. https://tokenharbor.ai/v1   (no trailing slash)
    LLM_API_KEY   the API key
    LLM_MODEL     e.g. deepseek-v4.1-flash:free

For AMD deployment, point LLM_BASE_URL at the AMD-hosted endpoint and set
LLM_MODEL to the AMD-served model name. See amd/ for deployment details.

A MOCK mode (LLM_MOCK=true) returns deterministic canned responses for
offline testing and CI — no network calls.
"""
import json
import os
import urllib.request
import urllib.error


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, base_url=None, api_key=None, model=None, timeout=120):
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.model = model or os.environ.get("LLM_MODEL", "")
        self.timeout = timeout
        self.mock = os.environ.get("LLM_MOCK", "").lower() in ("1", "true", "yes")
        if not self.mock and not (self.base_url and self.api_key and self.model):
            raise LLMError(
                "LLM not configured. Set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL "
                "or LLM_MOCK=true for offline testing."
            )

    def chat(self, messages, temperature=0.3, max_tokens=800):
        """Send chat messages, return the assistant's text reply."""
        if self.mock:
            return _mock_reply(messages)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "curl/8.0",  # egress proxy quirk: urllib UA gets 403s
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            raise LLMError(f"LLM API HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            raise LLMError(f"LLM API connection failed: {e.reason}")
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise LLMError(f"Unexpected LLM response shape: {str(data)[:300]}")

    def __repr__(self):
        target = "MOCK" if self.mock else f"{self.model} @ {self.base_url}"
        return f"LLMClient({target})"


def _mock_reply(messages):
    """Deterministic offline reply — clean advisor-style response from grounded facts."""
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break
    facts = ""
    if "GROUNDED FACTS" in last_user:
        facts = last_user.split("GROUNDED FACTS")[-1]
    # Parse the facts block into a clean response
    lines = [l.strip() for l in facts.strip().split("\n") if l.strip()]
    out = ["Based on your business profile, here is my assessment:\n"]
    for line in lines:
        # Skip raw formatting artifacts, keep the substance
        if line.startswith("Assumption:"):
            out.append(f"\n_{line}_")
        elif line.startswith("- ") or line.startswith("Business type:"):
            out.append(line)
        elif "monthly disposal cost" in line.lower() or "sustainability score" in line.lower():
            out.append(f"**{line}**")
        elif line and not line.startswith("("):
            out.append(line)
    out.append(
        "\nRecommendation: act on the highest-ROI lever first (packaging switch or "
        "composting), then lift diversion rate with staff training."
    )
    return "\n".join(out)
