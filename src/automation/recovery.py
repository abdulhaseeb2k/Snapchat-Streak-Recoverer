"""
Browser automation for Snapchat Streak Recovery.
Uses Playwright to fill and submit the support form.
"""

import asyncio
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
from src.constants import SNAPCHAT_FORM_URL


async def _fill_form(page, settings: dict, friend_username: str):
    """Fill a single Snapchat support form for one friend."""
    await page.goto(SNAPCHAT_FORM_URL, wait_until="domcontentloaded", timeout=60000)

    try:
        await page.wait_for_selector('#request_custom_fields_24281229', timeout=15000)
    except Exception as e:
        print(f"  ⚠ Form may not have loaded smoothly: {e}")

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
        except Exception:
            pass


def _resolve_profile_folder(app_settings: dict) -> str | None:
    """Determine the Chrome profile folder from app settings."""
    folder = app_settings.get("browser_profile_folder")
    if folder:
        return folder

    # Fallback: extract from display name
    display = app_settings.get("browser_profile", "")
    if "Chrome:" not in display:
        return None

    match = re.search(r'\(([^)]+)\)$', display)
    if match:
        return match.group(1)
    return display.replace("Chrome: ", "").strip() or None


def _find_chrome_executable() -> str | None:
    """Find the Chrome executable on Windows."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    return next((p for p in candidates if os.path.exists(p)), None)


async def run_recovery(
    settings: dict,
    friends_list: list[str],
    app_settings: dict,
    on_progress=None,
    on_complete=None,
    on_error=None,
):
    """
    Run the recovery automation.

    Args:
        settings: Profile settings dict (username, email, etc.)
        friends_list: List of friend usernames to recover
        app_settings: Global app settings (browser profile, etc.)
        on_progress: Optional callback(current_index, total, friend_username)
        on_complete: Optional callback()
        on_error: Optional callback(error_message)
    """
    async with async_playwright() as p:
        profile_folder = _resolve_profile_folder(app_settings)
        use_chrome_profile = bool(profile_folder)

        try:
            if use_chrome_profile:
                user_data_dir = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
                launch_args = [
                    f"--user-data-dir={user_data_dir}",
                    f"--profile-directory={profile_folder}",
                ]
                executable = _find_chrome_executable()
                print(f"🌐 Launching Chrome with profile: {profile_folder}")
                browser = await p.chromium.launch(
                    executable_path=executable,
                    headless=False,
                    args=launch_args,
                )
                context = await browser.new_context(no_viewport=True)
            else:
                print("🌐 Launching Test Browser (Chromium)...")
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()

            # Get a page
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()
            await page.bring_to_front()

            total = len(friends_list)
            for idx, friend in enumerate(friends_list):
                try:
                    if on_progress:
                        on_progress(idx, total, friend)

                    print(f"  [{idx+1}/{total}] Processing: {friend}")
                    await _fill_form(page, settings, friend)
                    print(f"  ✅ Form filled for {friend} — Solve Captcha & Submit")

                    # Wait for user to submit (poll until URL changes)
                    while True:
                        await asyncio.sleep(0.5)
                        if page.is_closed():
                            print("  ⛔ Page closed by user.")
                            return

                        if "/requests/new" not in page.url:
                            break

                        try:
                            if not await page.query_selector('form#new_request'):
                                break
                        except Exception:
                            break

                    print(f"  ✅ Submitted for {friend}!")
                    delay = float(settings.get('refresh_delay', 1.0))
                    await asyncio.sleep(delay)

                except Exception as e:
                    print(f"  ❌ Error for {friend}: {e}")
                    continue

            print("🎉 All friends processed! Closing browser...")
            if on_complete:
                on_complete()

            await asyncio.sleep(2)
            await browser.close()

        except Exception as e:
            err = str(e)
            if "Target page, context or browser has been closed" in err:
                print("  ⛔ Browser closed by user.")
            elif "already in use" in err.lower() or "lock" in err.lower():
                msg = "Google Chrome is already running. Please close it and try again."
                print(f"  ❌ {msg}")
                if on_error:
                    on_error(msg)
            else:
                print(f"  ❌ Automation Error: {e}")
                if on_error:
                    on_error(str(e))
