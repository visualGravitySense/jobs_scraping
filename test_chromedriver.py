#!/usr/bin/env python3
"""
Simple test script to check ChromeDriver setup
"""

import undetected_chromedriver as uc
import time

def test_chromedriver():
    print("Testing ChromeDriver setup...")
    
    try:
        # Try with version 137
        print("Attempting to setup ChromeDriver with version 137...")
        driver = uc.Chrome(version_main=137)
        print("✅ ChromeDriver setup successful!")
        
        # Test basic functionality
        print("Testing basic functionality...")
        driver.get("https://www.google.com")
        time.sleep(2)
        print(f"✅ Page title: {driver.title}")
        
        driver.quit()
        print("✅ ChromeDriver test completed successfully!")
        
    except Exception as e:
        print(f"❌ ChromeDriver setup failed: {e}")
        
        # Try with auto-detection
        try:
            print("\nTrying with auto-detection...")
            driver = uc.Chrome(version_main=None)
            print("✅ ChromeDriver setup successful with auto-detection!")
            
            driver.get("https://www.google.com")
            time.sleep(2)
            print(f"✅ Page title: {driver.title}")
            
            driver.quit()
            print("✅ ChromeDriver test completed successfully!")
            
        except Exception as e2:
            print(f"❌ Auto-detection also failed: {e2}")

if __name__ == "__main__":
    test_chromedriver() 