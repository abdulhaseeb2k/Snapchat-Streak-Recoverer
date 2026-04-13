import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def fill_form_for_friend(page, settings, friend_username):
    url = "https://help.snapchat.com/hc/en-us/requests/new?co=true&ticket_form_id=149423"
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    
    # Wait for the form to load (specifically checking for one of the main input fields)
    try:
        await page.wait_for_selector('#request_custom_fields_24281229', timeout=15000)
    except Exception as e:
        print(f"Warning: Form may not have loaded smoothly. Continuing anyway. {e}")

    # Field: Username
    try:
        await page.fill('#request_custom_fields_24281229', settings.get("username", ""), timeout=2000)
    except: pass
    
    # Field: Email
    try:
        await page.fill('#request_custom_fields_24335325', settings.get("email", ""), timeout=2000)
    except: pass
    
    # Field: Mobile number
    try:
        await page.fill('#request_custom_fields_24369716', settings.get("mobile_number", ""), timeout=2000)
    except: pass
    
    # Field: Device
    try:
        await page.fill('#request_custom_fields_24335345', settings.get("device", ""), timeout=2000)
    except: pass

    # Field: Friend's Username
    try:
        await page.fill('#request_custom_fields_24369736', friend_username, timeout=2000)
    except: pass

    # Field: When did you start having this issue? (Use today's date or yesterday)
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        await page.fill('#request_custom_fields_24369756', today, timeout=2000)
    except: pass

    # Field: Did you see the hourglass icon? (Assuming 'No' or select standard option)
    # usually it's a dropdown or radio. Let's not try to guess if it's not straightforward,
    # or just let the user fill that part.
    
    # Field: Description
    try:
        description_text = "My snapstreak disappeared recently without any reason. Please restore it."
        await page.fill('#request_description', description_text, timeout=2000)
    except: pass
    
    # We do NOT click submit automatically because of Captcha

async def run_recovery(settings, friends_list):
    async with async_playwright() as p:
        # Launching with headless=False so the user can interact
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Open a single page
        page = await context.new_page()

        for friend in friends_list:
            try:
                print(f"Navigating for friend: {friend}")
                await fill_form_for_friend(page, settings, friend)
                print(f"Filled form for {friend}. Please solve Captcha and Submit.")
                
                # Robust polling for successful submission
                while True:
                    await asyncio.sleep(0.5)
                    if page.is_closed():
                        print("Page was closed by user.")
                        return
                    
                    current_url = page.url
                    # If navigating away from the 'new' request page
                    if "/requests/new" not in current_url:
                        break
                    
                    # If the form itself is no longer in the DOM
                    try:
                        form_element = await page.query_selector('form#new_request, form[action*="/requests"]')
                        if not form_element:
                            break
                    except:
                         # Context destroyed usually means something is happening (refresh/submit)
                         # We can wait a cycle or break if we're sure it's gone
                         pass

                print(f"Form submitted safely for {friend}!")
                # Give the success page a brief moment before refreshing
                delay = float(settings.get('refresh_delay', 1.0))
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(f"Exception while processing {friend}: {e}")
                print("Skipping to next friend / trying to continue...")
                continue
                
        print("All selected friends processed! Closing browser in 3 seconds...")
        await asyncio.sleep(3)
        await browser.close()
