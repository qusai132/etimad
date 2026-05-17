from datetime import datetime, timezone
from typing import Optional
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.tender import Tender

logger = get_logger(__name__)
settings = get_settings()


TENDER_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="UTF-8" />
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; direction: rtl; background: #f5f5f5; margin: 0; padding: 0; }}
    .container {{ max-width: 680px; margin: 30px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.12); }}
    .header {{ background: #1a5276; color: #fff; padding: 28px 32px; }}
    .header h1 {{ margin: 0; font-size: 22px; }}
    .header p {{ margin: 6px 0 0; opacity: .85; font-size: 14px; }}
    .badge {{ display: inline-block; background: #27ae60; color: #fff; border-radius: 20px; padding: 4px 14px; font-size: 13px; margin-top: 10px; }}
    .body {{ padding: 28px 32px; }}
    .field {{ margin-bottom: 14px; }}
    .label {{ color: #666; font-size: 13px; margin-bottom: 2px; }}
    .value {{ color: #1a1a1a; font-size: 15px; font-weight: 500; }}
    .score-bar {{ background: #eee; border-radius: 4px; height: 8px; margin-top: 6px; }}
    .score-fill {{ background: #27ae60; border-radius: 4px; height: 8px; }}
    .cta {{ display: inline-block; background: #1a5276; color: #fff; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-size: 15px; margin-top: 20px; }}
    .footer {{ background: #f8f8f8; padding: 18px 32px; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>منافسة مطابقة لملف شركتكم</h1>
      <p>تم رصد منافسة حكومية جديدة على منصة اعتماد</p>
      <div class="badge">مطابقة بنسبة {score_pct}%</div>
    </div>
    <div class="body">
      <div class="field">
        <div class="label">عنوان المنافسة</div>
        <div class="value">{title}</div>
      </div>
      <div class="field">
        <div class="label">الجهة الحكومية</div>
        <div class="value">{entity}</div>
      </div>
      <div class="field">
        <div class="label">رقم المنافسة</div>
        <div class="value">{reference_number}</div>
      </div>
      <div class="field">
        <div class="label">النشاط</div>
        <div class="value">{activity}</div>
      </div>
      <div class="field">
        <div class="label">تاريخ النشر</div>
        <div class="value">{publish_date}</div>
      </div>
      <div class="field">
        <div class="label">آخر موعد لتقديم العروض</div>
        <div class="value">{last_offer_date}</div>
      </div>
      {price_block}
      <div class="field">
        <div class="label">سبب التطابق</div>
        <div class="value">{relevance_reason}</div>
        <div class="score-bar"><div class="score-fill" style="width:{score_pct}%"></div></div>
      </div>
      {details_block}
      <a href="{details_url}" class="cta">عرض تفاصيل المنافسة</a>
    </div>
    <div class="footer">
      تم إرسال هذا البريد تلقائياً من نظام مراقبة منصة اعتماد &bull; {sent_at}
    </div>
  </div>
</body>
</html>
"""


def _fmt_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "غير محدد"
    return dt.strftime("%Y/%m/%d")


def _build_html(tender: Tender) -> str:
    score_pct = int((tender.relevance_score or 0) * 100)
    price_block = ""
    if tender.document_price:
        price_block = (
            f'<div class="field"><div class="label">سعر الوثائق</div>'
            f'<div class="value">{tender.document_price:,.0f} {tender.document_price_currency or "SAR"}</div></div>'
        )
    details_block = ""
    if tender.tender_details:
        details_block = (
            f'<div class="field"><div class="label">وصف المنافسة</div>'
            f'<div class="value">{tender.tender_details[:400]}</div></div>'
        )

    return TENDER_EMAIL_TEMPLATE.format(
        title=tender.title or "غير محدد",
        entity=tender.entity or "غير محدد",
        reference_number=tender.reference_number,
        activity=tender.activity or "غير محدد",
        publish_date=_fmt_date(tender.publish_date),
        last_offer_date=_fmt_date(tender.last_offer_date),
        price_block=price_block,
        relevance_reason=tender.relevance_reason or "",
        score_pct=score_pct,
        details_block=details_block,
        details_url=tender.details_url or "#",
        sent_at=datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M UTC"),
    )


async def send_tender_alert(tender: Tender, recipient: Optional[str] = None) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("smtp_not_configured_skip_email")
        return False

    to_addr = recipient or settings.SMTP_USER
    html_body = _build_html(tender)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[اعتماد] منافسة مطابقة: {tender.title[:60]}"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("email_sent", tender_id=tender.id, to=to_addr)
        return True
    except Exception as e:
        logger.error("email_send_failed", tender_id=tender.id, error=str(e))
        return False
