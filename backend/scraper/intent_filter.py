from openai import OpenAI
from core.config import settings


SYSTEM_PROMPT = """You are a lead qualification AI. Your job is to analyze LinkedIn posts and determine if the author is ACTIVELY LOOKING FOR or EXPRESSING A NEED for a specific service.

Return a JSON object with:
- "qualified": true/false (true only if the person clearly needs the service)
- "confidence": 0.0 to 1.0 (how sure you are)
- "reason": short explanation (max 50 chars)

Qualify as YES if:
- Person explicitly says they need/want/looking for the service
- Person asks for recommendations/suggestions about the service
- Person complains about a problem that the service solves
- Person is hiring/freelancing for this service

Qualify as NO if:
- It's just a general post/news about the topic
- It's a promotion/ad by a provider
- It's vague or unrelated
- The person is offering the service, not looking for it"""


class IntentFilter:
    def __init__(self):
        key = settings.DEEPSEEK_API_KEY
        if key:
            self.client = OpenAI(
                api_key=key,
                base_url="https://api.deepseek.com/v1"
            )
        else:
            self.client = None

    def _has_intent_keywords(self, text: str, keyword: str) -> bool:
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        intent_signals = [
            "need", "want", "looking for", "recommend", "suggest",
            "help", "anyone know", "how to", "solution for",
            "looking to", "anyone using", "best", "affordable",
            "required", "seeking", "in need of", "who can",
            "hire", "freelancer", "service", "recommendation",
        ]
        if keyword_lower not in text_lower:
            return False
        return any(signal in text_lower for signal in intent_signals)

    def filter_leads(self, leads: list, keyword: str) -> list:
        if not leads:
            return []

        if not self.client:
            for lead in leads:
                match = self._has_intent_keywords(lead.post_text, keyword)
                lead.intent_score = 0.8 if match else 0.3
                lead.intent_reason = "Keyword match + intent signal" if match else "Low confidence"
            return [l for l in leads if l.intent_score >= 0.5]

        qualified = []
        batch = []
        for lead in leads:
            batch.append({
                "id": lead.id,
                "text": lead.post_text[:1000],
                "keyword": keyword,
            })

        if not batch:
            return []

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze these LinkedIn posts for '{keyword}' needs:\n" + "\n---\n".join([f"Post {i+1}: {b['text']}" for i, b in enumerate(batch)])}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            import json
            result = json.loads(response.choices[0].message.content)

            for i, lead in enumerate(leads):
                key = f"post_{i+1}"
                if key in result:
                    r = result[key]
                elif isinstance(result, dict) and "results" in result and i < len(result["results"]):
                    r = result["results"][i]
                else:
                    r = {"qualified": self._has_intent_keywords(lead.post_text, keyword), "confidence": 0.5, "reason": ""}

                if isinstance(r, dict):
                    lead.intent_score = r.get("confidence", 0.0) if r.get("qualified") else r.get("confidence", 0.0) * 0.3
                    lead.intent_reason = r.get("reason", "")

            qualified = [l for l in leads if l.intent_score >= 0.5]

        except Exception as e:
            print(f"AI filter error: {e}")
            for lead in leads:
                lead.intent_score = 0.6 if self._has_intent_keywords(lead.post_text, keyword) else 0.2
                lead.intent_reason = "Fallback: keyword match" if lead.intent_score >= 0.5 else "Fallback: low confidence"
            qualified = [l for l in leads if l.intent_score >= 0.5]

        if not qualified and leads:
            leads[0].intent_score = 0.5
            leads[0].intent_reason = "Fallback: included as best match"
            qualified = [leads[0]]

        return qualified


intent_filter = IntentFilter()
