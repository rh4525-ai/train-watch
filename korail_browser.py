from datetime import datetime

SEARCH_URL = "https://www.korail.com/ticket/search/general"

def _first(page, selectors):
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count():
            return locator
    raise RuntimeError("코레일 검색 입력 요소를 찾지 못했습니다.")

def search_trains(payload):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="ko-KR")
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=30000)
        departure = _first(page, ['input[placeholder*="출발"]', 'input[aria-label*="출발"]', 'input[name*="start"]'])
        arrival = _first(page, ['input[placeholder*="도착"]', 'input[aria-label*="도착"]', 'input[name*="end"]'])
        departure.fill(payload["departure_station"])
        arrival.fill(payload["arrival_station"])
        date = _first(page, ['input[type="date"]', 'input[placeholder*="날짜"]', 'input[aria-label*="날짜"]'])
        date.fill(payload["departure_date"])
        if payload.get("departure_time"):
            try:
                time_input = _first(page, ['input[type="time"]', 'input[placeholder*="시간"]', 'input[aria-label*="시간"]'])
                time_input.fill(payload["departure_time"])
            except RuntimeError:
                pass
        page.get_by_role("button", name="조회").click()
        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(1000)
        rows = page.locator("table tbody tr")
        results = []
        for i in range(min(rows.count(), 100)):
            text = " ".join(rows.nth(i).inner_text().split())
            if text:
                results.append({"raw": text})
        browser.close()
        return {"source": SEARCH_URL, "checked_at": datetime.now().isoformat(), "trains": results}
