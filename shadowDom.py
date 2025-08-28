#!/usr/bin/env python3
"""
Apex Trader Funding Booking Script
Automatically handles cookie consent and allows further automation
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class ApexTraderBooking:
    def __init__(self, headless=False):
        """Initialize the booking script with Chrome driver"""
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Add other useful options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Setup Chrome driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def handle_cookie_consent(self, timeout=15):
        """Handle the cookie consent dialog by clicking Reject All"""
        try:
            print("Looking for cookie consent dialog...")
            
            # Wait for the cookie consent dialog to appear
            wait = WebDriverWait(self.driver, timeout)
            
            # First, check for the shadow DOM container
            try:
                shadow_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cf_modal_container")))
                print("Cookie consent shadow DOM container detected")
                
                # Now try to access the shadow root and find the dialog
                shadow_root = self.driver.execute_script("return arguments[0].shadowRoot", shadow_container)
                if shadow_root:
                    print("Successfully accessed shadow root")
                    
                    # Look for the dialog inside the shadow root
                    dialog = shadow_root.find_element(By.CSS_SELECTOR, "dialog.cf_modal")
                    if dialog and dialog.get_attribute("open"):
                        print("Cookie consent dialog found in shadow DOM")
                        
                        # Now look for the Reject All button inside the shadow root
                        reject_button = self.find_reject_button_in_shadow(shadow_root)
                        
                        if reject_button:
                            print("Found Reject All button in shadow DOM, clicking it...")
                            # Click the button using JavaScript
                            self.driver.execute_script("arguments[0].click();", reject_button)
                            print("Clicked Reject All button")
                            
                            # Wait for the dialog to disappear
                            time.sleep(3)
                            
                            # Check if dialog is gone
                            try:
                                shadow_root.find_element(By.CSS_SELECTOR, "dialog.cf_modal[open]")
                                print("Dialog still visible, trying alternative approach...")
                                return self.handle_cookie_consent_alternative()
                            except:
                                print("Cookie consent dialog handled successfully!")
                                return True
                        else:
                            print("Reject All button not found in shadow DOM")
                            return self.handle_cookie_consent_alternative()
                    else:
                        print("Dialog not open in shadow DOM")
                        return True
                else:
                    print("Could not access shadow root")
                    return self.handle_cookie_consent_alternative()
                    
            except Exception as e:
                print(f"Shadow DOM approach failed: {e}")
                return self.handle_cookie_consent_alternative()
                
        except Exception as e:
            print(f"Error handling cookie consent: {e}")
            return self.handle_cookie_consent_alternative()
    
    def find_reject_button_in_shadow(self, shadow_root):
        """Find the Reject All button inside the shadow root"""
        try:
            # Try multiple selectors to find the reject button
            reject_button_selectors = [
                "#cf_consent-buttons__reject-all",  # Exact ID from HTML
                "button#cf_consent-buttons__reject-all",  # Button with exact ID
                ".cf_button--reject",  # Exact class from HTML
                "button.cf_button--reject",  # Button with exact class
                "button[class*='reject']",  # Partial class match
            ]
            
            for selector in reject_button_selectors:
                try:
                    button = shadow_root.find_element(By.CSS_SELECTOR, selector)
                    if button and button.is_displayed():
                        print(f"Found Reject All button using selector: {selector}")
                        return button
                except:
                    continue
            
            # If CSS selectors fail, try finding by text content
            try:
                all_buttons = shadow_root.find_elements(By.TAG_NAME, "button")
                for button in all_buttons:
                    if "reject" in button.text.lower():
                        print(f"Found button with 'reject' text: {button.text}")
                        return button
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"Error finding reject button in shadow root: {e}")
            return None
    
    def handle_cookie_consent_alternative(self):
        """Alternative method to handle cookie consent using JavaScript with Shadow DOM support"""
        try:
            print("Trying JavaScript approach with Shadow DOM support...")
            
            # Wait a bit more for the page to be fully loaded
            time.sleep(3)
            
            # JavaScript to handle Shadow DOM and find the reject button
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
            
            result = self.driver.execute_script(js_script)
            
            if result:
                print("Successfully clicked Reject All using JavaScript with Shadow DOM")
                time.sleep(3)
                
                # Check if dialog is gone by checking shadow DOM
                try:
                    shadow_container = self.driver.find_element(By.CSS_SELECTOR, "div.cf_modal_container")
                    shadow_root = self.driver.execute_script("return arguments[0].shadowRoot", shadow_container)
                    if shadow_root:
                        shadow_root.find_element(By.CSS_SELECTOR, "dialog.cf_modal[open]")
                        print("Dialog still visible after JavaScript click")
                        return False
                except:
                    print("Cookie consent dialog handled successfully with JavaScript!")
                    return True
            else:
                print("Could not find reject button even with JavaScript Shadow DOM approach")
                return False
                
        except Exception as e:
            print(f"JavaScript approach failed: {e}")
            return False
    
    def navigate_to_dashboard(self):
        """Navigate to the Apex Trader Funding dashboard"""
        url = "https://dashboard.apextraderfunding.com/member"
        print(f"Navigating to: {url}")
        
        try:
            self.driver.get(url)
            print("Page loaded successfully")
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Handle cookie consent
            if self.handle_cookie_consent():
                print("Ready for further automation!")
                return True
            else:
                print("Warning: Cookie consent handling failed")
                return False
                
        except Exception as e:
            print(f"Error navigating to dashboard: {e}")
            return False
    
    def wait_for_element(self, selector, timeout=10, by=By.CSS_SELECTOR):
        """Wait for an element to be present and visible"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, selector)))
            return element
        except Exception as e:
            print(f"Element not found: {selector}")
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")

def main():
    """Main function to run the booking script"""
    print("Starting Apex Trader Funding Booking Script...")
    
    # Create booking instance
    booking = ApexTraderBooking(headless=False)  # Set to True for headless mode
    
    try:
        # Navigate to dashboard and handle cookies
        if booking.navigate_to_dashboard():
            print("Successfully loaded dashboard and handled cookies!")
            print("You can now add your specific booking logic here.")
            
            # Keep the browser open for manual inspection or further automation
            input("Press Enter to close the browser...")
        else:
            print("Failed to properly load dashboard")
    
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        booking.close()

if __name__ == "__main__":
    main()
