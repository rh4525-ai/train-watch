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
        page = browser.new_page(locale="ko-KR", ignore_https_errors=True)
        response = page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=45000)
        if response and response.status >= 400:
            raise RuntimeError(f"코레일 페이지 응답 오류: HTTP {response.status}")
        page.wait_for_timeout(3000)
        departure = _first(page, ['input[placeholder*="출발"]', 'input[aria-label*="출발"]', 'input[name*="start"]', 'input[name*="dep"]', '[role="combobox"]'])
        arrival = _first(page, ['input[placeholder*="도착"]', 'input[aria-label*="도착"]', 'input[name*="end"]', 'input[name*="arr"]', '[role="combobox"]:nth-of-type(2)'])
        departure.fill(payload["departure_station"])
        arrival.fill(payload["arrival_station"])
        date = _first(page, ['input[type="date"]', 'input[placeholder*="날짜"]', 'input[aria-label*="날짜"]', 'input[name*="date"]'])
        date.fill(payload["departure_date"])
        if payload.get("departure_time"):
            try:
                time_input = _first(page, ['input[type="time"]', 'input[placeholder*="시간"]', 'input[aria-label*="시간"]'])
                time_input.fill(payload["departure_time"])
            except RuntimeError:
                pass
        search_button = page.get_by_role("button", name="조회").first
        if not search_button.count():
            search_button = page.get_by_text("조회", exact=True).first
        if not search_button.count():
            raise RuntimeError("코레일 조회 버튼을 찾지 못했습니다.")
        search_button.click()
        page.wait_for_timeout(5000)
        rows = page.locator("table tbody tr, table tr, [role='row'], li, article, [class*='train'], [class*='Train']")
        results = []
        seen = set()
        for i in range(min(rows.count(), 300)):
            text = " ".join(rows.nth(i).inner_text().split())
            if text and text not in seen and any(word in text.upper() for word in ("KTX", "SRT", "ITX", "무궁화", "새마을")):
                seen.add(text)
                results.append({"raw": text})
        if not results:
            body = " ".join(page.locator("body").inner_text().split())
            if any(word in body.upper() for word in ("KTX", "SRT", "ITX", "무궁화", "새마을")):
                results.append({"raw": body[:4000]})
            else:
                raise RuntimeError("코레일 조회는 완료됐지만 열차 결과 영역을 찾지 못했습니다.")
        browser.close()
        return {"source": SEARCH_URL, "checked_at": datetime.now().isoformat(), "trains": results}
