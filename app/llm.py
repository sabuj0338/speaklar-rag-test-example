from time import perf_counter

from groq import Groq


class GroqFallback:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = model

    def answer(self, query: str, context: list[dict]) -> tuple[str | None, float]:
        if not self.client:
            return None, 0.0
        prompt = (
            "You are an ecommerce sales assistant. Use only the provided catalog context. "
            "If the answer is not supported by the context, say 'I don't know.'\n\n"
            f"Context: {context}\n\nUser question: {query}"
        )
        started_at = perf_counter()
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=80,
        )
        groq_time_ms = (perf_counter() - started_at) * 1000
        return completion.choices[0].message.content.strip(), groq_time_ms
