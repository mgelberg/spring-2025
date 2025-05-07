from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def test_selenium():
    print("Setting up Chrome options...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    print("Initializing Chrome driver...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        print("Attempting to access a test website...")
        driver.get("https://www.google.com")
        print("Successfully loaded Google!")
        print(f"Page title: {driver.title}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    test_selenium()