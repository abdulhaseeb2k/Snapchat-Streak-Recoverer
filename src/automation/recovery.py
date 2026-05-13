"""
Browser automation for Snapchat Streak Recovery.
Uses Playwright to fill and submit the support form.
"""

import asyncio
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from playwright_recaptcha.recaptchav2.async_solver import AsyncSolver
from src.constants import SNAPCHAT_FORM_URL


async def _fill_form(page, settings: dict, friend_username: str):
    """Fill a single Snapchat support form for one friend."""
    await page.goto(SNAPCHAT_FORM_URL, wait_until="domcontentloaded", timeout=60000)

    try:
        await page.wait_for_selector('#request_custom_fields_24281229', timeout=15000)
    except Exception as e:
        print(f"  [WARN] Form may not have loaded smoothly: {e}")

    # Fill each field, silently skip on failure
    fields = [
        ('#request_custom_fields_24281229', settings.get("username", "")),
        ('#request_custom_fields_24335325', settings.get("email", "")),
        ('#request_custom_fields_24369716', settings.get("mobile_number", "")),
        ('#request_custom_fields_24335345', settings.get("device", "")),
        ('#request_custom_fields_24369736', friend_username),
        ('#request_custom_fields_24369756', datetime.now().strftime("%Y-%m-%d")),
        ('#request_description', "My snapstreak disappeared recently without any reason. Please restore it."),
    ]
    for selector, value in fields:
        try:
            await page.fill(selector, value, timeout=2000)
            await asyncio.sleep(0.5) # Slight delay between typing fields
        except Exception:
            pass

    # Try to solve CAPTCHA automatically
    try:
        print("  [INFO] Looking for reCAPTCHA...")
        solver = AsyncSolver(page)
        try:
            await solver.solve_recaptcha()
            print("  [OK] reCAPTCHA solved automatically!")
        except Exception as e:
            # If it fails, it's fine, user can still do it manually
            print(f"  [INFO] Auto-solve skipped: {e}")
    except Exception as e:
        print(f"  [DEBUG] Recaptcha solver init error: {e}")

    # Auto-submit the form
    try:
        print("  [INFO] Submitting form...")
        # Standard Zendesk/Snapchat submit button selectors
        submit_selectors = ['input[type="submit"]', 'button[type="submit"]', 'input[name="commit"]']
        for selector in submit_selectors:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    print("  [OK] Submit button clicked!")
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"  [WARN] Auto-submit failed: {e}")


async def run_recovery(
    settings: dict,
    friends_list: list[str],
    app_settings: dict,
    on_progress=None,
    on_complete=None,
    on_error=None,
):
    """
    Run the recovery automation using a clean browser context with stealth.

    Args:
        settings: Profile settings dict (username, email, etc.)
        friends_list: List of friend usernames to recover
        app_settings: Global app settings
        on_progress: Optional callback(current_index, total, friend_username)
        on_complete: Optional callback()
        on_error: Optional callback(error_message)
    """
    async with async_playwright() as p:
        browser = None
        context = None
        try:
            print("[INFO] Launching Recoverer Browser...")
            
            ext_path = app_settings.get("extension_path", "").strip()
            
            from src.constants import BROWSER_DATA_DIR, DEFAULT_EXTENSION_DIR
            
            if not ext_path and os.path.exists(DEFAULT_EXTENSION_DIR):
                ext_path = DEFAULT_EXTENSION_DIR
            
            if ext_path and os.path.isdir(ext_path):
                if not os.path.exists(BROWSER_DATA_DIR):
                    os.makedirs(BROWSER_DATA_DIR)
                    
                print(f"[INFO] Loading unpacked extension from: {ext_path}")
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=BROWSER_DATA_DIR,
                    headless=False,
                    args=[
                        f"--disable-extensions-except={ext_path}",
                        f"--load-extension={ext_path}"
                    ]
                )
                page = context.pages[0] if context.pages else await context.new_page()
            else:
                # Standard launch — reliable and clean
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                # Always open a fresh page
                page = await context.new_page()
            
            # Apply stealth to the page to look like a real user
            await Stealth().apply_stealth_async(page)
            
            await page.bring_to_front()

            total = len(friends_list)
            for idx, friend in enumerate(friends_list):
                try:
                    if on_progress:
                        on_progress(idx, total, friend)

                    print(f"  [{idx+1}/{total}] Processing: {friend}")
                    await _fill_form(page, settings, friend)
                    print(f"  [OK] Form filled for {friend} — Solve Captcha (if auto-solve skipped) & Submit")

                    # Wait for user to submit (poll until URL changes or page closed)
                    while True:
                        await asyncio.sleep(0.5)
                        if page.is_closed():
                            print("  [HALT] Page closed by user.")
                            return

                        if "/requests/new" not in page.url:
                            break

                        try:
                            if not await page.query_selector('form#new_request'):
                                break
                        except Exception:
                            break

                    print(f"  [DONE] Submitted for {friend}!")
                    delay = float(settings.get('refresh_delay', 1.0))
                    await asyncio.sleep(delay)

                except Exception as e:
                    print(f"  [ERROR] For {friend}: {e}")
                    continue

            print("[COMPLETE] All friends processed!")
            if on_complete:
                on_complete()

            await asyncio.sleep(2)
            if context:
                await context.close()
            if browser:
                await browser.close()

        except Exception as e:
            err = str(e)
            if "Target page, context or browser has been closed" in err:
                print("  [HALT] Browser closed by user.")
            else:
                print(f"  [ERROR] Automation Error: {e}")
                if on_error:
                    on_error(str(e))

