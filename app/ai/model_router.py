import time
import httpx
import os
from typing import Optional, List
from dataclasses import dataclass
from app.ai.data_sanitizer import data_sanitizer


def _load_env_file():
    env_paths = [
        r"C:\wahbi-platform\.env",
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
    ]
    for path in env_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        if value.strip() and key.strip() not in os.environ:
                            os.environ[key.strip()] = value.strip()
            break

_load_env_file()


@dataclass
class ModelResponse:
    text: str
    model_name: str
    tokens_input: int = 0
    tokens_output: int = 0
    processing_time_ms: int = 0
    was_sanitized: bool = False


class AIModelRouter:
    # Current Groq models (updated June 2025)
    GROQ_MODELS = [
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=20.0)
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()

        if self.gemini_key.startswith("gsk_"):
            self.gemini_key = ""

        print(f"  [AI Router] Groq: {'CONFIGURED' if len(self.groq_key) > 10 else 'not set'}")
        print(f"  [AI Router] Gemini: {'CONFIGURED' if len(self.gemini_key) > 10 else 'not set'}")
        print(f"  [AI Router] OpenRouter: {'CONFIGURED' if len(self.openrouter_key) > 10 else 'not set'}")
        if self.groq_key:
            print(f"  [AI Router] Groq models to try: {', '.join(self.GROQ_MODELS[:3])}")

    async def generate(self, system_prompt: str, user_message: str,
                       conversation_history: list = None, temperature: float = 0.7,
                       max_tokens: int = 500, require_local: bool = False) -> ModelResponse:
        start = time.time()

        # Try Groq with multiple model fallbacks
        if self.groq_key and len(self.groq_key) > 10:
            san_msg, ctx = data_sanitizer.sanitize(user_message)
            messages = [{"role": "system", "content": system_prompt}]
            if conversation_history:
                for h in conversation_history[-5:]:
                    messages.append(h)
            messages.append({"role": "user", "content": san_msg})

            for model_name in self.GROQ_MODELS:
                try:
                    print(f"  [AI] Trying Groq model: {model_name}...")
                    resp = await self.http_client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.groq_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model_name,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                        timeout=15.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    text = data_sanitizer.restore_response(text, ctx)
                    usage = data.get("usage", {})
                    ms = int((time.time() - start) * 1000)
                    print(f"  [AI] SUCCESS with {model_name} ({ms}ms)")
                    return ModelResponse(
                        text=text,
                        model_name=f"groq/{model_name}",
                        tokens_input=usage.get("prompt_tokens", 0),
                        tokens_output=usage.get("completion_tokens", 0),
                        processing_time_ms=ms,
                        was_sanitized=True,
                    )
                except httpx.HTTPStatusError as e:
                    error_body = e.response.text[:200]
                    print(f"  [AI] {model_name} failed: {e.response.status_code} - {error_body}")
                    if "decommissioned" in error_body or "not found" in error_body:
                        continue  # Try next model
                    elif "rate_limit" in error_body:
                        print(f"  [AI] Rate limited. Waiting 2 seconds...")
                        import asyncio
                        await asyncio.sleep(2)
                        continue
                    else:
                        break  # Other error, don't retry
                except httpx.TimeoutException:
                    print(f"  [AI] {model_name} timed out")
                    continue
                except Exception as e:
                    print(f"  [AI] {model_name} error: {str(e)[:100]}")
                    continue

        # Try Gemini
        if self.gemini_key and len(self.gemini_key) > 10:
            try:
                san_msg, ctx = data_sanitizer.sanitize(user_message)
                prompt = f"{system_prompt}\n\nUser: {san_msg}"
                print(f"  [AI] Trying Gemini...")
                resp = await self.http_client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
                    },
                    timeout=15.0,
                )
                resp.raise_for_status()
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                text = data_sanitizer.restore_response(text, ctx)
                ms = int((time.time() - start) * 1000)
                print(f"  [AI] SUCCESS with Gemini ({ms}ms)")
                return ModelResponse(text=text, model_name="gemini/1.5-flash",
                                     processing_time_ms=ms, was_sanitized=True)
            except Exception as e:
                print(f"  [AI] Gemini error: {str(e)[:200]}")

        # Try OpenRouter
        if self.openrouter_key and len(self.openrouter_key) > 10:
            try:
                san_msg, ctx = data_sanitizer.sanitize(user_message)
                messages = [{"role": "system", "content": system_prompt}]
                messages.append({"role": "user", "content": san_msg})
                print(f"  [AI] Trying OpenRouter...")
                resp = await self.http_client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openrouter_key}", "Content-Type": "application/json"},
                    json={"model": "meta-llama/llama-3.1-70b-instruct", "messages": messages,
                          "temperature": temperature, "max_tokens": max_tokens},
                    timeout=15.0,
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]
                text = data_sanitizer.restore_response(text, ctx)
                ms = int((time.time() - start) * 1000)
                print(f"  [AI] SUCCESS with OpenRouter ({ms}ms)")
                return ModelResponse(text=text, model_name="openrouter/llama-3.1-70b",
                                     processing_time_ms=ms, was_sanitized=True)
            except Exception as e:
                print(f"  [AI] OpenRouter error: {str(e)[:200]}")

        # Fallback
        print(f"  [AI] All APIs failed. Using smart fallback.")
        return ModelResponse(
            text=self._generate_fallback(user_message, system_prompt),
            model_name="fallback/template",
            processing_time_ms=int((time.time() - start) * 1000),
        )

    def _generate_fallback(self, user_message: str, system_prompt: str) -> str:
        msg = user_message.lower()
        arabic_chars = sum(1 for c in msg if '\u0600' <= c <= '\u06FF')
        is_arabic = arabic_chars > len(msg) * 0.3
        if is_arabic:
            return "\u0623\u0647\u0644\u0627\u064b \u0648\u0633\u0647\u0644\u0627\u064b! \u0643\u064a\u0641 \u0623\u0642\u062f\u0631 \u0623\u0633\u0627\u0639\u062f\u0643 \u0627\u0644\u064a\u0648\u0645\u061f \U0001f60a"
        if any(w in msg for w in ["problem", "issue", "complaint", "refund", "wrong"]):
            return "I'm sorry to hear about your experience. Let me help resolve this. Could you share your order details?"
        if any(w in msg for w in ["menu", "dish", "food", "order", "recommend"]):
            return "Thank you for your interest! We'd love to help you find the perfect meal. What type of cuisine are you in the mood for?"
        if any(w in msg for w in ["price", "cost", "how much"]):
            return "For pricing, please specify what you're interested in. All our prices include 15% VAT."
        return "Hello! Thank you for reaching out. How can I assist you today? \U0001f60a"

    async def close(self):
        await self.http_client.aclose()


model_router = AIModelRouter()