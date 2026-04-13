import asyncio
import os
from playwright.async_api import async_playwright
from datetime import datetime
import tkinter.messagebox as mb

async def fill_form_for_friend(page, settings, friend_username):
    url = "https://help.snapchat.com/hc/en-us/requests/new?co=true&ticket_form_id=149423"
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    
    # Wait for the form to load
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

    # Field: Issue Date
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        await page.fill('#request_custom_fields_24369756', today, timeout=2000)
    except: pass

    # Field: Description
    try:
        description_text = "My snapstreak disappeared recently without any reason. Please restore it."
        await page.fill('#request_description', description_text, timeout=2000)
    except: pass

async def run_recovery(settings, friends_list, app_settings):
    async with async_playwright() as p:
        # Try getting direct folder name first
        profile_folder = app_settings.get("browser_profile_folder")
        
        # If folder name is missing but display name is available, try extracting from parentheses
        if not profile_folder:
            display_name = app_settings.get("browser_profile", "")
            if "Chrome:" in display_name:
                import re
                match = re.search(r'\(([^)]+)\)$', display_name)
                if match:
                    profile_folder = match.group(1)
                else:
                    # Fallback for simple "Chrome: Default" format
                    profile_folder = display_name.replace("Chrome: ", "").strip()
        
        is_persistent = False
        user_data_dir = None
        launch_args = []
        
        if profile_folder and profile_folder != "Test Browser (No Profile)":
            user_data_dir = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
            launch_args.extend([
                f"--user-data-dir={user_data_dir}",
                f"--profile-directory={profile_folder}"
            ])
            is_persistent = True

        try:
            if is_persistent:
                # Find Chrome path automatically
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
                ]
                executable = next((p for p in chrome_paths if os.path.exists(p)), None)
                
                print(f"Launching Chrome via CLI: {profile_folder}...")
                # We use launch() instead of launch_persistent_context to avoid the CDP attachment hang
                browser = await p.chromium.launch(
                    executable_path=executable,
                    headless=False,
                    args=launch_args
                )
                context = await browser.new_context(no_viewport=True)
            else:
                print("Launching fresh Test Browser (Chromium)...")
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()

            # In persistent context, Chromium often opens a default page automatically
            print("DEBUG: Getting browser page...")
            if is_persistent and context.pages:
                page = context.pages[0]
                print("DEBUG: Using existing page")
            else:
                page = await context.new_page()
                print("DEBUG: Created new page")

            # Ensure page is focused
            print("DEBUG: Bringing page to front...")
            await page.bring_to_front()
            
            print(f"DEBUG: Processing {len(friends_list)} friends...")

            for friend in friends_list:
                try:
                    print(f"Navigating for friend: {friend}")
                    await fill_form_for_friend(page, settings, friend)
                    print(f"Filled form for {friend}. Please solve Captcha and Submit.")
                    
                    while True:
                        await asyncio.sleep(0.5)
                        if page.is_closed():
                            print("Page was closed by user.")
                            return
                        
                        if "/requests/new" not in page.url:
                            break
                        
                        try:
                            # Check if form still exists
                            form_exists = await page.query_selector('form#new_request')
                            if not form_exists:
                                break
                        except:
                            break

                    print(f"Form submitted safely for {friend}!")
                    delay = float(settings.get('refresh_delay', 1.0))
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    print(f"Exception while processing {friend}: {e}")
                    continue
                    
            print("All selected friends processed! Closing browser in 3 seconds...")
            await asyncio.sleep(3)
            
            if is_persistent:
                await context.close()
            else:
                await browser.close()

        except Exception as e:
            err_msg = str(e)
            if "Target page, context or browser has been closed" in err_msg:
                print("Browser was closed by user.")
            elif "User Data Directory is already in use" in err_msg or "lock" in err_msg.lower():
                print("\n" + "!"*50)
                print("ERROR: Google Chrome is already running!")
                print("Please CLOSE Google Chrome completely and try again.")
                print("!"*50 + "\n")
                mb.showerror("Chrome Already Open", "Google Chrome is currently using this profile.\n\nPlease CLOSE Google Chrome completely before starting recovery.")
            else:
                print(f"Automation Error: {e}")
                mb.showerror("Automation Error", f"An error occurred: {e}")
