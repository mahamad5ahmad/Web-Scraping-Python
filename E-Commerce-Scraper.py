import random
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sqlite3

class BestBuyScraper:
    def __init__(self):
        self.base_url = "https://www.bestbuy.com"
        self.products = []
        self._setup_driver()
        self.db_name = "products.db"
        self._setup_database()

    def _select_country(self, country="United States"):
        """
        Handle the country selection page
        Args:
            country (str): Either "United States" or "Canada"
        """
        try:
            # Wait for country selection page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Choose a country')]"))
            )
            
            # Click the appropriate country button
            country_button = self.driver.find_element(
                By.XPATH, f"//button[contains(., '{country}')]"
            )
            country_button.click()
            
            # Wait for navigation to complete
            time.sleep(2)
            
        except TimeoutException:
            print("Country selection page not detected, proceeding anyway")
        except Exception as e:
            print(f"Error selecting country: {str(e)}")
    
    def _setup_database(self):
        """Initialize SQLite database with error handling."""
        try:
            self.db_conn = sqlite3.connect(self.db_name)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL,
                rating REAL,
                review_count INTEGER,
                url TEXT UNIQUE,
                image_url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            self.db_conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            raise
    def _setup_driver(self):
        """Configure ChromeDriver with anti-detection measures"""
        chrome_options = Options()
        
        # Basic options
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        
        # Anti-bot detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Disable images for faster loading
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        
        # Disable GPU if causing issues
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            service = Service(r'C:\Users\user\Downloads\chromedriver-win64\chromedriver.exe') #your chrome driver path
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Mask selenium detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self._select_country()
        except Exception as e:
            raise Exception(f"Failed to initialize WebDriver: {str(e)}")

    def search_products(self, search_term="phones", max_pages=1):
        """Search for products using search page"""
        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/site/searchpage.jsp?st={search_term}"
            print(f"Scraping page {page}: {url}")
            
            try:
                self.driver.get(url)
                
                # Wait for either the products or the "no results" message
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".sku-item, .no-results-message")
                        )
                    )
                except TimeoutException:
                    print(f"Timeout waiting for products on page {page}")
                    continue
                
                # Check for "no results" message
                if self.driver.find_elements(By.CSS_SELECTOR, ".no-results-message"):
                    print("No results found for this search")
                    break
                
                # Scroll and load all products
                self._scroll_page()
                time.sleep(random.uniform(1, 3))  # Random delay
                
                # Parse the page
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                self._parse_products(soup)
                
            except Exception as e:
                print(f"Error scraping page {page}: {str(e)}")
                continue

    def _scroll_page(self):
        """Scroll page to load all products with random behavior"""
        scroll_pause_time = random.uniform(0.5, 1.5)
        
        # Random scroll pattern
        for _ in range(random.randint(2, 4)):
            scroll_height = random.randint(500, 1500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            time.sleep(scroll_pause_time)
        
        # Final scroll to bottom
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

    def _parse_products(self, soup):
        """Parse product items with updated selectors"""
        product_items = soup.select('.sku-item:not(.sku-item--disabled)')
        
        if not product_items:
            print("Warning: No products found on this page")
            return
            
        for item in product_items:
            try:
                product = {
                    'name': self._get_text(item, 'h4.sku-title a'),
                    'price': self._get_text(item, 'div.priceView-customer-price span, div.priceView-hero-price span'),
                    'rating': self._get_text(item, 'div.ratings-reviews span[aria-hidden="true"]'),
                    'review_count': self._get_text(item, 'span.c-reviews'),
                    'url': self._get_url(item),
                    'image_url': self._get_image(item)
                }
                
                # Only add if we have basic info
                if product['name'] and product['price']:
                    self.products.append(product)
            except Exception as e:
                print(f"Error parsing product: {str(e)}")
                continue

    def _get_text(self, parent, selector):
        """Safely extract text from selector"""
        element = parent.select_one(selector)
        return element.get_text(strip=True) if element else None

    def _get_url(self, item):
        """Extract product URL"""
        link = item.select_one('a.image-link')
        if link and 'href' in link.attrs:
            return self.base_url + link['href']
        return None

    def _get_image(self, item):
        """Extract product image URL"""
        img = item.select_one('img.product-image')
        if img and 'src' in img.attrs:
            return img['src']
        return None

    def clean_data(self):
        """Clean and structure the scraped data"""
        if not self.products:
            return pd.DataFrame()
            
        df = pd.DataFrame(self.products)
        
        # Clean price
        if 'price' in df.columns:
            df['price'] = df['price'].str.replace(r'[^\d.]', '', regex=True)
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # Clean rating
        if 'rating' in df.columns:
            df['rating'] = df['rating'].str.extract(r'(\d\.\d)')[0]
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        
        # Clean review count
        if 'review_count' in df.columns:
            df['review_count'] = df['review_count'].str.replace(r'[^\d]', '', regex=True)
            df['review_count'] = pd.to_numeric(df['review_count'], errors='coerce').fillna(0).astype(int)
        
        return df

    def save_to_csv(self, filename='products.csv'):
        """Save data to CSV file"""
        df = self.clean_data()
        if df.empty:
            print("No data to save")
            return
            
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    
    def save_to_database(self):
        """Save data to database with improved error handling."""
        df = self.clean_data()
        if df.empty:
            print("No data to save to database")
            return 0
            
        try:
            cursor = self.db_conn.cursor()
            records = df.to_dict('records')
            
            cursor.executemany('''
            INSERT OR IGNORE INTO products 
            (name, price, rating, review_count, url, image_url)
            VALUES (:name, :price, :rating, :review_count, :url, :image_url)
            ''', records)
            
            self.db_conn.commit()
            print(f"Inserted {cursor.rowcount} records into database")
            return cursor.rowcount
            
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return 0
    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()


if __name__ == "__main__":
    try:
        scraper = BestBuyScraper()
        
        # Try different search terms if needed
        search_terms = ["phones", 
                    #    "laptops",
                    #    "headphones",
                          ]
        
        for term in search_terms:
            print(f"\nSearching for: {term}")
            scraper.search_products(search_term=term)
            if scraper.products:
                break
                
        if not scraper.products:
            print("Warning: No products were scraped from any search term")
        else:
            scraper.save_to_csv()
            scraper.save_to_database()
            
            # Print sample results
            print("\nSample products found:")
            for product in scraper.products[:3]:
                print(f"{product['name']} - {product['price']}")
                
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        scraper.close()