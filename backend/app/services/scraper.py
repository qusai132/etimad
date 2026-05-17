import re
from datetime import datetime, timezone
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.tender import TenderCreate

logger = get_logger(__name__)
settings = get_settings()

BASE_URL = "https://tenders.etimad.sa"
TENDER_LIST_URL = f"{BASE_URL}/Tender/AllTendersForVisitor"


def _parse_arabic_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    date_str = date_str.strip()
    patterns = [
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ]
    for fmt in patterns:
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_price(price_str: Optional[str]) -> Optional[float]:
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", price_str.replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _extract_text(soup: BeautifulSoup, selector: str, index: int = 0) -> Optional[str]:
    elements = soup.select(selector)
    if elements and len(elements) > index:
        return elements[index].get_text(strip=True) or None
    return None


def _extract_detail_field(soup: BeautifulSoup, label_text: str) -> Optional[str]:
    for row in soup.select("tr"):
        cells = row.select("td, th")
        for i, cell in enumerate(cells):
            if label_text in cell.get_text():
                if i + 1 < len(cells):
                    return cells[i + 1].get_text(strip=True) or None
    for div in soup.select(".row, .form-group, .detail-row"):
        text = div.get_text()
        if label_text in text:
            parts = text.split(label_text, 1)
            if len(parts) > 1:
                value = parts[1].strip().split("\n")[0].strip()
                if value:
                    return value
    return None


class EtimadScraper:
    def __init__(self):
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.SCRAPER_HEADLESS,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        self._context = await self._browser.new_context(
            locale="ar-SA",
            timezone_id="Asia/Riyadh",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        return self

    async def __aexit__(self, *args):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        await self._playwright.stop()

    async def _new_page(self) -> Page:
        page = await self._context.new_page()
        page.set_default_timeout(settings.SCRAPER_TIMEOUT_MS)
        return page

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get_total_pages(self, page: Page) -> int:
        url = f"{TENDER_LIST_URL}?PageSize=50"
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        content = await page.content()
        soup = BeautifulSoup(content, "lxml")

        last_page = 1

        # Strategy 1: look for PageNumber in any anchor href
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            m = re.search(r"[Pp]age[Nn]umber=(\d+)", href)
            if m:
                last_page = max(last_page, int(m.group(1)))

        # Strategy 2: digit-only text in pagination elements
        for el in soup.select("li a, li button, .pagination *, [class*='page'] *"):
            text = el.get_text(strip=True)
            if text.isdigit():
                last_page = max(last_page, int(text))

        # Strategy 3: look for "من X صفحة" / "of X pages" text in the page
        page_text = soup.get_text()
        for pattern in [r"من\s+(\d+)\s+صفح", r"of\s+(\d+)\s+page", r"Page\s+\d+\s+of\s+(\d+)"]:
            m = re.search(pattern, page_text, re.IGNORECASE)
            if m:
                last_page = max(last_page, int(m.group(1)))

        # Strategy 4: try navigating to a high page number to find the ceiling
        if last_page == 1:
            for probe in [999, 100, 50, 20, 10, 5]:
                probe_url = f"{TENDER_LIST_URL}?PageNumber={probe}&PageSize=50"
                await page.goto(probe_url, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                probe_content = await page.content()
                probe_soup = BeautifulSoup(probe_content, "lxml")
                # Check if the page has tender links (not empty/redirect)
                probe_links = [
                    a["href"] for a in probe_soup.select("a[href]")
                    if any(p in a.get("href", "") for p in ["/Tender/Details/", "/Tender/OpenTenderDetails/", "TenderId="])
                ]
                if probe_links:
                    last_page = probe
                    break

        logger.info("total_pages_found", pages=last_page)
        return last_page

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get_tender_links_from_page(self, page: Page, page_number: int) -> list[str]:
        url = f"{TENDER_LIST_URL}?PageNumber={page_number}&PageSize=50"
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        # Scroll to trigger any lazy-loaded content
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        content = await page.content()
        soup = BeautifulSoup(content, "lxml")

        links = set()
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            # Match any href that looks like a tender detail URL
            if any(pat in href for pat in [
                "/Tender/Details/",
                "/Tender/OpenTenderDetails/",
                "/Tender/TenderDetails/",
                "TenderId=",
                "tenderId=",
                "tender_id=",
            ]):
                full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                # Strip anchors/fragments
                full_url = full_url.split("#")[0]
                links.add(full_url)

        # Also try JS-rendered hrefs via evaluate
        try:
            js_hrefs: list[str] = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(h => h.includes('/Tender/Details/') ||
                                 h.includes('/Tender/OpenTenderDetails/') ||
                                 h.includes('TenderId='))
            """)
            for href in js_hrefs:
                links.add(href.split("#")[0])
        except Exception:
            pass

        logger.info("links_found_on_page", page=page_number, count=len(links))
        return list(links)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _scrape_tender_details(self, page: Page, details_url: str) -> Optional[TenderCreate]:
        await page.goto(details_url, wait_until="networkidle")

        # Click "تفاصيل المنافسة" button if present
        try:
            btn = await page.query_selector("a:has-text('تفاصيل المنافسة'), button:has-text('تفاصيل المنافسة')")
            if btn:
                await btn.click()
                await page.wait_for_load_state("networkidle")
        except Exception:
            pass

        raw_html = await page.content()
        soup = BeautifulSoup(raw_html, "lxml")

        title = (
            _extract_text(soup, "h1, h2, .tender-title, [class*='title']")
            or _extract_text(soup, ".panel-title")
            or "غير محدد"
        )

        ref = (
            _extract_detail_field(soup, "رقم المنافسة")
            or _extract_detail_field(soup, "الرقم المرجعي")
            or _extract_detail_field(soup, "Reference Number")
        )

        if not ref:
            m = re.search(r"TenderId=([^&]+)", details_url)
            if m:
                ref = m.group(1)
            else:
                m2 = re.search(r"/Details/([^/\?]+)", details_url)
                ref = m2.group(1) if m2 else details_url.split("/")[-1]

        entity = (
            _extract_detail_field(soup, "الجهة الحكومية")
            or _extract_detail_field(soup, "اسم الجهة")
            or _extract_detail_field(soup, "الجهة")
        )

        activity = (
            _extract_detail_field(soup, "النشاط")
            or _extract_detail_field(soup, "نشاط المنافسة")
        )

        tender_type = (
            _extract_detail_field(soup, "نوع المنافسة")
            or _extract_detail_field(soup, "نوع العطاء")
        )

        publish_date_str = (
            _extract_detail_field(soup, "تاريخ النشر")
            or _extract_detail_field(soup, "تاريخ الإعلان")
        )
        last_enquiry_str = (
            _extract_detail_field(soup, "آخر موعد للاستفسار")
            or _extract_detail_field(soup, "تاريخ آخر استفسار")
        )
        last_offer_str = (
            _extract_detail_field(soup, "آخر موعد لاستلام العروض")
            or _extract_detail_field(soup, "تاريخ آخر عرض")
            or _extract_detail_field(soup, "الموعد النهائي")
        )
        award_date_str = _extract_detail_field(soup, "تاريخ الترسية")

        price_str = (
            _extract_detail_field(soup, "سعر الوثائق")
            or _extract_detail_field(soup, "قيمة الوثائق")
        )

        tender_details = (
            _extract_detail_field(soup, "وصف المنافسة")
            or _extract_detail_field(soup, "تفاصيل المنافسة")
        )
        purpose = _extract_detail_field(soup, "الغرض من المنافسة")
        conditions = _extract_detail_field(soup, "شروط التأهيل")
        location = (
            _extract_detail_field(soup, "الموقع")
            or _extract_detail_field(soup, "منطقة التنفيذ")
        )
        quantity = _extract_detail_field(soup, "الكمية")

        currency = None
        if price_str:
            if "ريال" in price_str or "SAR" in price_str:
                currency = "SAR"

        return TenderCreate(
            reference_number=str(ref).strip(),
            title=title.strip(),
            entity=entity,
            activity=activity,
            tender_type=tender_type,
            publish_date=_parse_arabic_date(publish_date_str),
            last_enquiry_date=_parse_arabic_date(last_enquiry_str),
            last_offer_date=_parse_arabic_date(last_offer_str),
            award_date=_parse_arabic_date(award_date_str),
            document_price=_parse_price(price_str),
            document_price_currency=currency,
            tender_details=tender_details,
            purpose=purpose,
            conditions=conditions,
            location=location,
            quantity=quantity,
            details_url=details_url,
            raw_html=raw_html[:200000],  # cap at 200KB
            scraped_at=datetime.now(timezone.utc),
        )

    async def scrape_incremental(self, known_refs: set[str], on_tender_scraped=None) -> list[TenderCreate]:
        """Scrape only new tenders. Stops when a full page has no new tenders."""
        results: list[TenderCreate] = []

        async with self:
            list_page = await self._new_page()
            try:
                total_pages = await self._get_total_pages(list_page)
            except Exception as e:
                logger.error("failed_to_get_total_pages", error=str(e))
                total_pages = 10  # check up to 10 pages as safety limit

            for page_num in range(1, total_pages + 1):
                logger.info("incremental_scraping_page", page=page_num, total=total_pages)
                try:
                    links = await self._get_tender_links_from_page(list_page, page_num)
                except Exception as e:
                    logger.error("page_scrape_failed", page=page_num, error=str(e))
                    break

                if not links:
                    break

                detail_page = await self._new_page()
                page_new_count = 0
                try:
                    for link in links:
                        try:
                            tender = await self._scrape_tender_details(detail_page, link)
                            if tender:
                                if tender.reference_number not in known_refs:
                                    results.append(tender)
                                    known_refs.add(tender.reference_number)
                                    page_new_count += 1
                                    if on_tender_scraped:
                                        await on_tender_scraped(tender)
                        except Exception as e:
                            logger.error("tender_scrape_failed", url=link, error=str(e))
                finally:
                    await detail_page.close()

                if page_new_count == 0:
                    logger.info("incremental_caught_up", stopped_at_page=page_num)
                    break

            await list_page.close()

        logger.info("incremental_scrape_done", new_tenders=len(results))
        return results

    async def scrape_all(self, on_tender_scraped=None) -> list[TenderCreate]:
        results: list[TenderCreate] = []

        async with self:
            list_page = await self._new_page()
            try:
                total_pages = await self._get_total_pages(list_page)
            except Exception as e:
                logger.error("failed_to_get_total_pages", error=str(e))
                total_pages = 1

            for page_num in range(1, total_pages + 1):
                logger.info("scraping_page", page=page_num, total=total_pages)
                try:
                    links = await self._get_tender_links_from_page(list_page, page_num)
                except Exception as e:
                    logger.error("page_scrape_failed", page=page_num, error=str(e))
                    continue

                detail_page = await self._new_page()
                try:
                    for link in links:
                        try:
                            tender = await self._scrape_tender_details(detail_page, link)
                            if tender:
                                results.append(tender)
                                if on_tender_scraped:
                                    await on_tender_scraped(tender)
                        except Exception as e:
                            logger.error("tender_scrape_failed", url=link, error=str(e))
                finally:
                    await detail_page.close()

            await list_page.close()

        return results
