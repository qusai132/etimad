import json
from datetime import datetime, timezone
from typing import Optional
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.tender import Tender

logger = get_logger(__name__)
settings = get_settings()


class TenderMatcher:
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self._client:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def _build_company_profile(self) -> str:
        activities = ", ".join(settings.company_activities_list)
        return (
            f"اسم الشركة: {settings.COMPANY_NAME}\n"
            f"مجالات النشاط: {activities}"
        )

    def _build_tender_summary(self, tender: Tender) -> str:
        parts = [
            f"عنوان المنافسة: {tender.title}",
            f"الجهة: {tender.entity or 'غير محدد'}",
            f"النشاط: {tender.activity or 'غير محدد'}",
            f"نوع المنافسة: {tender.tender_type or 'غير محدد'}",
        ]
        if tender.tender_details:
            parts.append(f"تفاصيل: {tender.tender_details[:500]}")
        if tender.purpose:
            parts.append(f"الغرض: {tender.purpose[:300]}")
        return "\n".join(parts)

    async def match_tender(self, tender: Tender) -> dict:
        if not settings.OPENAI_API_KEY:
            return self._keyword_match(tender)

        company_profile = self._build_company_profile()
        tender_summary = self._build_tender_summary(tender)

        prompt = f"""أنت محلل مناقصات متخصص. قم بتحليل ما إذا كانت المنافسة التالية مناسبة للشركة المذكورة.

ملف الشركة:
{company_profile}

تفاصيل المنافسة:
{tender_summary}

قم بالإجابة بصيغة JSON فقط بالشكل التالي:
{{
  "is_relevant": true/false,
  "confidence_score": 0.0-1.0,
  "reason": "سبب مختصر باللغة العربية"
}}

اعتبر المنافسة مناسبة إذا كانت تتعلق بأي من مجالات الشركة أو مجالات مرتبطة بها."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=300,
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "is_relevant": bool(result.get("is_relevant", False)),
                "relevance_score": float(result.get("confidence_score", 0.0)),
                "relevance_reason": str(result.get("reason", "")),
            }
        except Exception as e:
            logger.error("openai_match_failed", tender_id=tender.id, error=str(e))
            return self._keyword_match(tender)

    def _keyword_match(self, tender: Tender) -> dict:
        activities = settings.company_activities_list
        text = " ".join(filter(None, [
            tender.title,
            tender.activity,
            tender.entity,
            tender.tender_details,
            tender.purpose,
            tender.tender_type,
        ])).lower()

        matched_keywords = []
        for activity in activities:
            if activity.lower() in text:
                matched_keywords.append(activity)

        score = min(len(matched_keywords) / max(len(activities), 1), 1.0)
        is_relevant = score >= settings.RELEVANCE_THRESHOLD

        reason = (
            f"تطابق الكلمات المفتاحية: {', '.join(matched_keywords)}"
            if matched_keywords
            else "لم يتم العثور على تطابق مع مجالات الشركة"
        )

        return {
            "is_relevant": is_relevant,
            "relevance_score": round(score, 2),
            "relevance_reason": reason,
        }

    async def run_matching(self, tenders: list[Tender]) -> list[Tender]:
        updated = []
        for tender in tenders:
            try:
                result = await self.match_tender(tender)
                tender.is_relevant = result["is_relevant"]
                tender.relevance_score = result["relevance_score"]
                tender.relevance_reason = result["relevance_reason"]
                tender.matched_at = datetime.now(timezone.utc)
                updated.append(tender)
                logger.info(
                    "tender_matched",
                    tender_id=tender.id,
                    is_relevant=tender.is_relevant,
                    score=tender.relevance_score,
                )
            except Exception as e:
                logger.error("match_failed", tender_id=tender.id, error=str(e))
        return updated
