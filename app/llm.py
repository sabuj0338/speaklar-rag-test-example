from time import perf_counter

from groq import Groq


class GroqFallback:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = model

    def answer(self, query: str, context: list[dict]) -> tuple[str | None, float]:
        if not self.client:
            return None, 0.0

        # Build context from full_text (Knowledge_Bank format) or metadata (legacy format)
        context_texts = []
        for item in context:
            text = item.get("full_text") or item.get("metadata") or item.get("text", "")
            context_texts.append(text)
        context_str = "\n".join(context_texts)

        prompt = (
            "তুমি একজন বাংলাদেশী ই-কমার্স সহকারী। শুধুমাত্র নিচের তথ্য থেকে বাংলায় উত্তর দাও। "
            "উত্তর সংক্ষিপ্ত ও সহায়ক হতে হবে। "
            "যদি তথ্যে উত্তর না থাকে, বলো 'দুঃখিত, আমাদের তালিকায় এটি নেই।'\n\n"
            f"তথ্য:\n{context_str}\n\n"
            f"প্রশ্ন: {query}"
        )
        started_at = perf_counter()
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=150,
        )
        groq_time_ms = (perf_counter() - started_at) * 1000
        return completion.choices[0].message.content.strip(), groq_time_ms
