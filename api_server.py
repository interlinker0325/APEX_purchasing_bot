from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
import sys
import uuid
import random
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global session storage for multiple users
sessions = {}

def create_session():
    """Create a new session with unique ID"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'status': 'ready',  # ready, processing, completed, error, stopped
        'logs': [],
        'current_iteration': 0,
        'total_iterations': 0,
        'should_stop': False,
        'driver': None,
        'created_at': datetime.now(),
        'last_activity': datetime.now()
    }
    return session_id

def get_session(session_id):
    """Get session by ID, create if doesn't exist"""
    if session_id not in sessions:
        return None
    sessions[session_id]['last_activity'] = datetime.now()
    return sessions[session_id]

def cleanup_old_sessions():
    """Clean up sessions older than 1 hour"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in sessions.items():
        if (current_time - session_data['last_activity']).total_seconds() > 3600:  # 1 hour
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        cleanup_session(session_id)

def cleanup_session(session_id):
    """Clean up a specific session"""
    if session_id in sessions:
        session = sessions[session_id]
        if session['driver']:
            try:
                session['driver'].quit()
            except:
                pass
        del sessions[session_id]

def add_log(session_id, message):
    """Add a log message with timestamp to specific session"""
    session = get_session(session_id)
    if not session:
        return
        
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f'[{timestamp}] {message}'
    session['logs'].append(log_entry)
    print(f"[Session {session_id[:8]}...] {log_entry}")  # Also print to console

def reset_session(session_id):
    """Reset session to initial state"""
    session = get_session(session_id)
    if not session:
        return
        
    session['status'] = 'ready'
    session['logs'] = []
    session['current_iteration'] = 0
    session['total_iterations'] = 0
    session['should_stop'] = False
    if session['driver']:
        try:
            session['driver'].quit()
        except:
            pass
    session['driver'] = None

def handle_cookie_consent(driver, session_id):
    """Handle cookie consent dialog using shadow DOM"""
    add_log(session_id, "Looking for cookie consent dialog...")
    try:
        wait = WebDriverWait(driver, 10)
        
        # First, check for the shadow DOM container
        try:
            shadow_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cf_modal_container")))
            add_log(session_id, "Cookie consent shadow DOM container detected")
            
            # Now try to access the shadow root and find the dialog
            shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_container)
            if shadow_root:
                add_log(session_id, "Successfully accessed shadow root")
                
                # Look for the dialog inside the shadow root
                dialog = shadow_root.find_element(By.CSS_SELECTOR, "dialog.cf_modal")
                if dialog and dialog.get_attribute("open"):
                    add_log(session_id, "Cookie consent dialog found in shadow DOM")
                    
                    # Try multiple selectors to find the reject button
                    reject_button_selectors = [
                        "#cf_consent-buttons__reject-all",
                        "button#cf_consent-buttons__reject-all",
                        ".cf_button--reject",
                        "button.cf_button--reject",
                        "button[class*='reject']",
                    ]
                    
                    reject_button = None
                    for selector in reject_button_selectors:
                        try:
                            button = shadow_root.find_element(By.CSS_SELECTOR, selector)
                            if button and button.is_displayed():
                                add_log(session_id, f"Found Reject All button using selector: {selector}")
                                reject_button = button
                                break
                        except:
                            continue
                    
                    # If CSS selectors fail, try finding by text content
                    if not reject_button:
                        try:
                            all_buttons = shadow_root.find_elements(By.TAG_NAME, "button")
                            for button in all_buttons:
                                if "reject" in button.text.lower():
                                    add_log(session_id, f"Found button with 'reject' text: {button.text}")
                                    reject_button = button
                                    break
                        except:
                            pass
                    
                    if reject_button:
                        add_log(session_id, "Found Reject All button in shadow DOM, clicking it...")
                        # Click the button using JavaScript
                        driver.execute_script("arguments[0].click();", reject_button)
                        add_log(session_id, "Clicked Reject All button")
                        time.sleep(3)
                    else:
                        add_log(session_id, "Reject All button not found in shadow DOM")
                else:
                    add_log(session_id, "Dialog not open in shadow DOM")
            else:
                add_log(session_id, "Could not access shadow root")
                
        except Exception as e:
            add_log(session_id, f"Shadow DOM approach failed: {e}")
            
    except Exception as e:
        add_log(session_id, f"Error handling cookie consent: {e}")

    add_log(session_id, "Cookie consent handling completed, continuing with script...")

def run_automation(session_id, username, password, card_number, card_expired_month, card_expired_year, card_code, loop_count, coupon_code, selected_accounts):
    """Run the automation process in a separate thread for specific session"""
    try:
        add_log(session_id, "Starting automation process...")
        session = get_session(session_id)
        if not session:
            return
            
        session['status'] = 'processing'
        session['total_iterations'] = loop_count
        
        # Load coupon code from environment
        add_log(session_id, f"Using coupon code: {coupon_code}")
        
        # Initialize Chrome driver with undetected-chromedriver
        add_log(session_id, "Initializing Chrome driver...")
        
        # Use undetected-chromedriver with version override
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Try to force download of correct ChromeDriver version
        driver = uc.Chrome(options=options, version_main=139)
        
        session['driver'] = driver
        
        # Navigate to login page
        add_log(session_id, "Navigating to login page...")
        driver.get('https://dashboard.apextraderfunding.com/member/')
        time.sleep(5)
        
        # Handle cookie consent
        handle_cookie_consent(driver, session_id)
        
        # Check if stop was requested
        if session['should_stop']:
            add_log(session_id, "Process stopped by user before login.")
            driver.quit()
            session['status'] = 'stopped'
            return
        
        # Login
        add_log(session_id, "Logging in...")
        user_name = driver.find_element(By.ID, "amember-login")
        user_name.send_keys(username)
        pwd = driver.find_element(By.ID, "amember-pass")
        pwd.send_keys(password)
        time.sleep(1)
        
        login_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Login"]')
        login_button.click()
        time.sleep(5)
        
        # Check if login was successful
        try:
            # Wait a bit more for page to load
            time.sleep(3)
            
            # Look for login error messages first
            try:
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, .am-error, .alert, .message")
                if error_elements:
                    for element in error_elements:
                        error_text = element.text.strip()
                        if error_text and ("invalid" in error_text.lower() or "incorrect" in error_text.lower() or "failed" in error_text.lower()):
                            add_log(session_id, f"❌ Login failed: {error_text}")
                            session['status'] = 'error'
                            print(f"[DEBUG] Login failed - setting status to error for session {session_id}")
                            driver.quit()
                            return
            except:
                pass
            
            # Check current URL and page content
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            # If still on login page or contains login elements, login failed
            if ("login" in current_url or "member" not in current_url or 
                "amember-login" in page_source or "amember-pass" in page_source):
                add_log(session_id, "❌ Login failed: Still on login page after login attempt")
                add_log(session_id, f"Current URL: {current_url}")
                session['status'] = 'error'
                print(f"[DEBUG] Login failed - setting status to error for session {session_id}")
                driver.quit()
                return
            else:
                add_log(session_id, "✅ Login successful!")
        except Exception as e:
            add_log(session_id, f"❌ Error checking login status: {str(e)}")
            session['status'] = 'error'
            driver.quit()
            return
        
        add_log(session_id, f"Starting purchase loop for {loop_count} accounts...")
        add_log(session_id, f"Selected account types: {', '.join(selected_accounts)}")
        
        # Main workflow loop
        for iteration in range(loop_count):
            if session['should_stop']:
                add_log(session_id, "Purchase process stopped by user.")
                break
                
            session['current_iteration'] = iteration + 1
            add_log(session_id, f"🔄 Processing account {iteration + 1}/{loop_count}")
            
            try:
                # Select account type for this iteration (cycle through selected accounts)
                account_type = selected_accounts[iteration % len(selected_accounts)]
                account_url = f'https://dashboard.apextraderfunding.com/signup/{account_type}'
                
                # Navigate to signup page
                driver.get(account_url)
                time.sleep(5)
                add_log(session_id, f"Navigated to signup page for account {iteration + 1} ({account_type})")

                # Use coupon code from environment file
                coupon = driver.find_element(By.ID, 'coupon-0')
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", coupon)
                coupon.clear()
                coupon.send_keys(coupon_code)
                time.sleep(2)
                add_log(session_id, f"Entered coupon code '{coupon_code}' for account {iteration + 1}")

                agree = driver.find_element(By.ID, '_i_agree-page-0-0-0')
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", agree)
                driver.execute_script("arguments[0].click();", agree)
                time.sleep(2)
                add_log(session_id, f"Agreed to terms for account {iteration + 1}")

                next_button = driver.find_element(By.ID,'_qf_page-0_next-0')
                next_button.click()
                time.sleep(3)
                add_log(session_id, f"Clicked next button for account {iteration + 1}")

                card_number_input = driver.find_element(By.ID, "cc_number")
                card_number_input.clear()
                card_number_input.send_keys(card_number)
                time.sleep(2)
                add_log(session_id, f"Entered card number for account {iteration + 1}")

                card_ex_month_select = driver.find_element(By.ID, "m-0")
                select_month = Select(card_ex_month_select)
                select_month.select_by_value(card_expired_month)
                time.sleep(2)
                add_log(session_id, f"Selected expiration month for account {iteration + 1}")

                card_ex_year_select = driver.find_element(By.ID, "y-0")
                select_year = Select(card_ex_year_select)
                select_year.select_by_value(card_expired_year)
                time.sleep(2)
                add_log(session_id, f"Selected expiration year for account {iteration + 1}")

                card_code_button = driver.find_element(By.ID, "cc_code")
                card_code_button.clear()
                card_code_button.send_keys(card_code)
                time.sleep(2)
                add_log(session_id, f"Entered card code for account {iteration + 1}")

                pay_button = driver.find_element(By.ID, "qfauto-0")
                driver.execute_script("arguments[0].click();", pay_button)
                time.sleep(5)
                add_log(session_id, f"Clicked pay button for account {iteration + 1}")
                
                # Wait for processing
                time.sleep(3)
                add_log(session_id, f"Account {iteration + 1} ({account_type}) purchased successfully!")
                
            except Exception as e:
                add_log(session_id, f"Error processing account {iteration + 1}: {str(e)}")
                continue
        
        if session['should_stop']:
            add_log(session_id, "🛑 Purchase process stopped by user.")
            session['status'] = 'stopped'
        else:
            add_log(session_id, "✅ All purchases completed successfully!")
            add_log(session_id, f"📊 Summary: {loop_count} accounts processed")
            session['status'] = 'completed'
        
        # Ensure status is properly set before cleanup
        print(f"[DEBUG] Final status set to: {session['status']}")
        
    except Exception as e:
        add_log(session_id, f"❌ Automation error: {str(e)}")
        session['status'] = 'error'
    finally:
        if session and session['driver']:
            try:
                add_log(session_id, "🔄 Closing browser...")
                session['driver'].quit()
                add_log(session_id, "✅ Browser closed successfully")
            except Exception as e:
                add_log(session_id, f"⚠️ Error closing browser: {str(e)}")
            session['driver'] = None
            
            # Final status update to ensure frontend gets the final state
            print(f"[DEBUG] Final session status: {session['status']}")
            add_log(session_id, f"🏁 Process finished with status: {session['status']}")

@app.route('/api/purchase', methods=['POST'])
def start_purchase():
    """Start the purchase process with data from frontend"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['username', 'password', 'cardNumber', 'cvv', 'expiryMonth', 'expiryYear', 'numberOfAccounts', 'selectedAccounts']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new session for this user
        session_id = create_session()
        
        # Extract data
        username = data['username']
        password = data['password']
        card_number = data['cardNumber']
        card_expired_month = data['expiryMonth']
        card_expired_year = data['expiryYear']
        card_code = data['cvv']
        loop_count = int(data['numberOfAccounts'])
        selected_accounts = data['selectedAccounts']
        
        # Optional coupon code from frontend, fallback to .env file
        coupon_code = data.get('couponCode', os.getenv('COUPON_CODE', 'JAYPELLE'))
        
        # Start automation in a separate thread
        thread = threading.Thread(
            target=run_automation,
            args=(session_id, username, password, card_number, card_expired_month, card_expired_year, card_code, loop_count, coupon_code, selected_accounts)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Purchase process started successfully',
            'status': 'processing',
            'session_id': session_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """Get current status and logs for specific session"""
    session = get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Debug logging
    print(f"[DEBUG] Status request for session {session_id}: {session['status']}")
        
    return jsonify({
        'status': session['status'],
        'current_iteration': session['current_iteration'],
        'total_iterations': session['total_iterations'],
        'logs': session['logs']
    }), 200

@app.route('/api/stop/<session_id>', methods=['POST'])
def stop_purchase(session_id):
    """Stop the current purchase process for specific session"""
    try:
        session = get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
            
        session['should_stop'] = True
        add_log(session_id, "Stop request received from frontend")
        
        # If driver is active, try to close it
        if session['driver']:
            try:
                session['driver'].quit()
                session['driver'] = None
                add_log(session_id, "Browser closed successfully")
            except:
                add_log(session_id, "Error closing browser")
        
        session['status'] = 'stopped'
        
        return jsonify({
            'message': 'Stop request processed',
            'status': 'stopped'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error stopping process: {str(e)}'}), 500

@app.route('/api/reset/<session_id>', methods=['POST'])
def reset(session_id):
    """Reset the status for specific session"""
    reset_session(session_id)
    return jsonify({'message': 'Status reset successfully'}), 200

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions (for debugging)"""
    cleanup_old_sessions()  # Clean up expired sessions
    
    active_sessions = {}
    for session_id, session_data in sessions.items():
        active_sessions[session_id] = {
            'status': session_data['status'],
            'created_at': session_data['created_at'].isoformat(),
            'last_activity': session_data['last_activity'].isoformat(),
            'current_iteration': session_data['current_iteration'],
            'total_iterations': session_data['total_iterations']
        }
    
    return jsonify({
        'active_sessions': active_sessions,
        'total_sessions': len(active_sessions)
    }), 200

if __name__ == '__main__':
    print("Starting APEX Purchasing Bot API Server...")
    print("Server will be available at http://localhost:8000")
    print("Multi-user support enabled - each user gets a unique session")
    app.run(host='0.0.0.0', port=8000, debug=True)
