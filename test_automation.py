import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def test_form():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        url = "https://help.snapchat.com/hc/en-us/requests/new?co=true&ticket_form_id=149423"
        print(f"Navigating to {url}")
        await page.goto(url)
        
        print("Waiting for network idle")
        await page.wait_for_load_state("networkidle")

        print("Taking snapshot of form inputs")
        inputs = await page.evaluate('''() => {
            const elms = document.querySelectorAll('input, textarea, select');
            return Array.from(elms).map(e => {
                let lbl = "";
                if(e.id) {
                    const l = document.querySelector(`label[for="${e.id}"]`);
                    if(l) lbl = l.innerText;
                }
                return {tag: e.tagName, type: e.type, id: e.id, name: e.name, cls: e.className, label: lbl.replace(/\\n/g, " ").trim()};
            });
        }''')
        
        import pprint
        pprint.pprint(inputs)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_form())
