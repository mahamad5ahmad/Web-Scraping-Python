# Web Scraping & Data Processing Task

## Overview
A robust Python web scraper that extracts product information from Best Buy's website. The tool:
- Automatically handles country selection (US/Canada)
- Navigates JavaScript-rendered content using Selenium
- Implements anti-bot detection measures
- Outputs clean product data to CSV/sqlite3
- Features intelligent retry logic for reliability

## Setup

Prerequisites

    Python 3.8+
    Chrome browser installed
    ChromeDriver matching your Chrome version

Setup

    Clone this repository: git clone https://github.com/yourusername/bestbuy-scraper.git
    Install the required dependencies:pip install -r requirements.txt
    Download ChromeDriver

        1- Get the version matching your Chrome browser from https://chromedriver.chromium.org/downloads

        2- Place the chromedriver executable in your PATH or in the project directory Usage

## Usage
Run the E-Commerce-Scraper with default settings:
python E-Commerce-Scraper.py

## Notes

Output:
The script generates a CSV file and db file.

## Future Improvements

Here are potential enhancements to make the scraper more robust and feature-rich:
1. Enhanced Error Handling & Recovery
2. Advanced Anti-Detection Measures
3. Data Processing Enhancements
4. Storage & Deployment Improvements
5. Extended E-commerce Features
6. Maintenance & Monitoring
7. User Experience
8. Legal Compliance