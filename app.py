import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')
coupon_code = os.getenv('COUPON_CODE')
card_number = os.getenv('CARD_NUMBER')
card_expired_month = os.getenv('CARD_EXPIRED_MONTH')
card_expired_year = os.getenv('CARD_EXPIRED_YEAR')
card_code = os.getenv('CARD_CODE')
loop_count = int(os.getenv('LOOP_COUNT', '1'))

driver = uc.Chrome()

driver.get('https://dashboard.apextraderfunding.com/member/')
time.sleep(5)

# Handle cookie consent using shadow DOM functionality
print("Looking for cookie consent dialog...")
try:
    wait = WebDriverWait(driver, 10)
    
    # First, check for the shadow DOM container
    try:
        shadow_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cf_modal_container")))
        print("Cookie consent shadow DOM container detected")
        
        # Now try to access the shadow root and find the dialog
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_container)
        if shadow_root:
            print("Successfully accessed shadow root")
            
            # Look for the dialog inside the shadow root
            dialog = shadow_root.find_element(By.CSS_SELECTOR, "dialog.cf_modal")
            if dialog and dialog.get_attribute("open"):
                print("Cookie consent dialog found in shadow DOM")
                
                # Try multiple selectors to find the reject button
                reject_button_selectors = [
                    "#cf_consent-buttons__reject-all",  # Exact ID from HTML
                    "button#cf_consent-buttons__reject-all",  # Button with exact ID
                    ".cf_button--reject",  # Exact class from HTML
                    "button.cf_button--reject",  # Button with exact class
                    "button[class*='reject']",  # Partial class match
                ]
                
                reject_button = None
                for selector in reject_button_selectors:
                    try:
                        button = shadow_root.find_element(By.CSS_SELECTOR, selector)
                        if button and button.is_displayed():
                            print(f"Found Reject All button using selector: {selector}")
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
                                print(f"Found button with 'reject' text: {button.text}")
                                reject_button = button
                                break
                    except:
                        pass
                
                if reject_button:
                    print("Found Reject All button in shadow DOM, clicking it...")
                    # Click the button using JavaScript
                    driver.execute_script("arguments[0].click();", reject_button)
                    print("Clicked Reject All button")
                    
                    # Wait for the dialog to disappear
                    time.sleep(3)
                    
                    # Check if dialog is gone
                    try:
                        shadow_root.find_element(By.CSS_SELECTOR, "dialog.cf_modal[open]")
                        print("Dialog still visible, trying JavaScript approach...")
                        
                        # JavaScript fallback approach
                        js_script = """
                        // Function to find reject button in shadow DOM
                        function findRejectButtonInShadow() {
                            // First, find the shadow DOM container
                            const shadowContainer = document.querySelector('div.cf_modal_container');
                            if (!shadowContainer) {
                                console.log('Shadow container not found');
                                return null;
                            }
                            
                            // Access the shadow root
                            const shadowRoot = shadowContainer.shadowRoot;
                            if (!shadowRoot) {
                                console.log('Shadow root not accessible');
                                return null;
                            }
                            
                            // Look for the dialog
                            const dialog = shadowRoot.querySelector('dialog.cf_modal');
                            if (!dialog || !dialog.hasAttribute('open')) {
                                console.log('Dialog not found or not open');
                                return null;
                            }
                            
                            // Try multiple ways to find the reject button inside shadow root
                            let rejectButton = shadowRoot.querySelector('#cf_consent-buttons__reject-all') ||
                                             shadowRoot.querySelector('button#cf_consent-buttons__reject-all') ||
                                             shadowRoot.querySelector('.cf_button--reject') ||
                                             shadowRoot.querySelector('button.cf_button--reject') ||
                                             shadowRoot.querySelector('button[class*="reject"]') ||
                                             Array.from(shadowRoot.querySelectorAll('button')).find(btn => 
                                                 btn.textContent.trim() === 'Reject All' || 
                                                 btn.textContent.includes('Reject All')
                                             );
                            
                            return rejectButton;
                        }
                        
                        // Try to find and click the reject button
                        const rejectButton = findRejectButtonInShadow();
                        
                        if (rejectButton && rejectButton.offsetParent !== null) {  // Check if visible
                            // Scroll to the button
                            rejectButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            
                            // Try clicking
                            rejectButton.click();
                            return true;
                        }
                        
                        return false;
                        """
                        
                        result = driver.execute_script(js_script)
                        if result:
                            print("Successfully clicked Reject All using JavaScript with Shadow DOM")
                            time.sleep(3)
                        else:
                            print("Could not find reject button even with JavaScript approach")
                    except:
                        print("Cookie consent dialog handled successfully!")
                else:
                    print("Reject All button not found in shadow DOM, trying JavaScript approach...")
                    
                    # JavaScript fallback approach
                    print("Trying JavaScript approach with Shadow DOM support...")
                    time.sleep(3)
                    
                    js_script = """
                    // Function to find reject button in shadow DOM
                    function findRejectButtonInShadow() {
                        // First, find the shadow DOM container
                        const shadowContainer = document.querySelector('div.cf_modal_container');
                        if (!shadowContainer) {
                            console.log('Shadow container not found');
                            return null;
                        }
                        
                        // Access the shadow root
                        const shadowRoot = shadowContainer.shadowRoot;
                        if (!shadowRoot) {
                            console.log('Shadow root not accessible');
                            return null;
                        }
                        
                        // Look for the dialog
                        const dialog = shadowRoot.querySelector('dialog.cf_modal');
                        if (!dialog || !dialog.hasAttribute('open')) {
                            console.log('Dialog not found or not open');
                            return null;
                        }
                        
                        // Try multiple ways to find the reject button inside shadow root
                        let rejectButton = shadowRoot.querySelector('#cf_consent-buttons__reject-all') ||
                                         shadowRoot.querySelector('button#cf_consent-buttons__reject-all') ||
                                         shadowRoot.querySelector('.cf_button--reject') ||
                                         shadowRoot.querySelector('button.cf_button--reject') ||
                                         shadowRoot.querySelector('button[class*="reject"]') ||
                                         Array.from(shadowRoot.querySelectorAll('button')).find(btn => 
                                             btn.textContent.trim() === 'Reject All' || 
                                             btn.textContent.includes('Reject All')
                                         );
                        
                        return rejectButton;
                    }
                    
                    // Try to find and click the reject button
                    const rejectButton = findRejectButtonInShadow();
                    
                    if (rejectButton && rejectButton.offsetParent !== null) {  // Check if visible
                        // Scroll to the button
                        rejectButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        
                        // Try clicking
                        rejectButton.click();
                        return true;
                    }
                    
                    return false;
                    """
                    
                    result = driver.execute_script(js_script)
                    if result:
                        print("Successfully clicked Reject All using JavaScript with Shadow DOM")
                        time.sleep(3)
                    else:
                        print("Could not find reject button even with JavaScript approach")
            else:
                print("Dialog not open in shadow DOM")
        else:
            print("Could not access shadow root")
            
    except Exception as e:
        print(f"Shadow DOM approach failed: {e}")
        print("Trying JavaScript approach with Shadow DOM support...")
        time.sleep(3)
        
        js_script = """
        // Function to find reject button in shadow DOM
        function findRejectButtonInShadow() {
            // First, find the shadow DOM container
            const shadowContainer = document.querySelector('div.cf_modal_container');
            if (!shadowContainer) {
                console.log('Shadow container not found');
                return null;
            }
            
            // Access the shadow root
            const shadowRoot = shadowContainer.shadowRoot;
            if (!shadowRoot) {
                console.log('Shadow root not accessible');
                return null;
            }
            
            // Look for the dialog
            const dialog = shadowRoot.querySelector('dialog.cf_modal');
            if (!dialog || !dialog.hasAttribute('open')) {
                console.log('Dialog not found or not open');
                return null;
            }
            
            // Try multiple ways to find the reject button inside shadow root
            let rejectButton = shadowRoot.querySelector('#cf_consent-buttons__reject-all') ||
                             shadowRoot.querySelector('button#cf_consent-buttons__reject-all') ||
                             shadowRoot.querySelector('.cf_button--reject') ||
                             shadowRoot.querySelector('button.cf_button--reject') ||
                             shadowRoot.querySelector('button[class*="reject"]') ||
                             Array.from(shadowRoot.querySelectorAll('button')).find(btn => 
                                 btn.textContent.trim() === 'Reject All' || 
                                 btn.textContent.includes('Reject All')
                             );
            
            return rejectButton;
        }
        
        // Try to find and click the reject button
        const rejectButton = findRejectButtonInShadow();
        
        if (rejectButton && rejectButton.offsetParent !== null) {  // Check if visible
            // Scroll to the button
            rejectButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Try clicking
            rejectButton.click();
            return true;
        }
        
        return false;
        """
        
        result = driver.execute_script(js_script)
        if result:
            print("Successfully clicked Reject All using JavaScript with Shadow DOM")
            time.sleep(3)
        else:
            print("Could not find reject button even with JavaScript approach")
            
except Exception as e:
    print(f"Error handling cookie consent: {e}")

print("Cookie consent handling completed, continuing with script...")
time.sleep(1)

# The cookie consent is now handled automatically by the shadow DOM functionality above
# No need for manual pyautogui clicks or the old commented approach

user_name = driver.find_element(By.ID, "amember-login")
user_name.send_keys(username)
pwd = driver.find_element(By.ID, "amember-pass")
pwd.send_keys(password)
time.sleep(1)

login_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Login"]')
login_button.click()
time.sleep(5)

print(f"Starting automation loop - will repeat {loop_count} times")

# Main workflow loop
for iteration in range(loop_count):
    print(f"\n=================== Starting Iteration {iteration + 1}/{loop_count} ===================")
    
    try:
        # Navigate to signup page
        driver.get('https://dashboard.apextraderfunding.com/signup/50k-Tradovate')
        time.sleep(5)
        print(f"Iteration {iteration + 1}: Navigated to signup page")

        coupon = driver.find_element(By.ID, 'coupon-0')
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", coupon)
        coupon.clear()  # Clear any existing text
        coupon.send_keys(coupon_code)
        time.sleep(2)
        print(f"Iteration {iteration + 1}: Entered coupon code")

        agree = driver.find_element(By.ID, '_i_agree-page-0-0-0')
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", agree)
        driver.execute_script("arguments[0].click();", agree)
        time.sleep(2)
        print(f"Iteration {iteration + 1}: Agreed to terms")


        next_button = driver.find_element(By.ID,'_qf_page-0_next-0')
        next_button.click()
        time.sleep(3)
        print(f"Iteration {iteration + 1}: Clicked next button")

        card_number_input = driver.find_element(By.ID, "cc_number")
        card_number_input.clear()  # Clear any existing text
        card_number_input.send_keys(card_number)
        time.sleep(2)
        print(f"Iteration {iteration + 1}: Entered card number")

        card_ex_month_select = driver.find_element(By.ID, "m-0")
        select_month = Select(card_ex_month_select)
        select_month.select_by_value(card_expired_month)
        time.sleep(2)
        print(f"Iteration {iteration + 1}: Selected expiration month")

        card_ex_year_select = driver.find_element(By.ID, "y-0")
        select_year = Select(card_ex_year_select)
        select_year.select_by_value(card_expired_year)
        time.sleep(2)
        print(f"Iteration {iteration + 1}: Selected expiration year")

        card_code_button = driver.find_element(By.ID, "cc_code")
        card_code_button.clear()  # Clear any existing text
        card_code_button.send_keys(card_code)
        time.sleep(2)
        print(f"Iteration {iteration + 1}: Entered card code")

        pay_button = driver.find_element(By.ID, "qfauto-0")
        driver.execute_script("arguments[0].click();", pay_button)
        time.sleep(5)
        print(f"Iteration {iteration + 1}: Clicked pay button")
        
        # Wait for processing (you may need to adjust this based on the response)
        time.sleep(3)
        print(f"Iteration {iteration + 1}: Completed successfully")
    except Exception as e:
        print(f"Error in iteration {iteration + 1}: {str(e)}")
        print(f"Continuing to next iteration...")
        continue

print(f"\n=================== All {loop_count} iterations completed ===================")

# Keep browser open for manual inspection
input("Press Enter to close the browser...")
driver.quit()
