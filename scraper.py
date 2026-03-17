from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import random


def start_driver():
    service = Service(ChromeDriverManager().install())

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_pages(keyword="laptops", max_pages=5):
    return [
        f"https://www.amazon.com/s?k={keyword}&page={page}"
        for page in range(1, max_pages + 1)
    ]


def scrape_products(keyword="laptops", max_pages=5):
    urls = get_pages(keyword, max_pages)
    driver = start_driver()

    all_data = []

    try:
        for url in urls:
            driver.get(url)
            sleep(random.uniform(2, 5))

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
                )
            )

            soup = BeautifulSoup(driver.page_source, "lxml")
            products = soup.select("div[data-component-type='s-search-result']")

            for product in products:
                try:
                    title_elem = product.select_one("h2 span")
                    price_elem = product.select_one(".a-price .a-offscreen")
                    rating_elem = product.select_one("span.a-icon-alt")
                    reviews_elem = product.select_one("span.a-size-mini")

                    stock_elem = product.select_one("span.a-size-base.a-color-price")
                    asin = product.get("data-asin")
                    img_tag = product.select_one("img.s-image")

                    all_data.append({
                        "Name": title_elem.text.strip() if title_elem else "No title",
                        "Price": price_elem.text.strip() if price_elem else "No price",
                        "Rating": rating_elem.text.strip() if rating_elem else "No rating",
                        "Reviews": reviews_elem.text.strip() if reviews_elem else "No reviews",
                        "Stock": stock_elem.text.strip() if stock_elem else "Not specified",
                        "Link": f"https://www.amazon.com/dp/{asin}" if asin else "No link",
                        "Image": img_tag.get("src") if img_tag else "No image",
                        "Keyword": keyword
                    })

                except Exception as e:
                    print(f"Error in product: {e}")
                    continue

    finally:
        driver.quit()

    return all_data


def data_frame(keyword="laptops", max_pages=5):
    data = scrape_products(keyword, max_pages)
    return pd.DataFrame(data)


def clean_data(df):
    df = df.drop_duplicates()

    df["Price"] = (
        df["Price"]
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)

    df["Rating"] = df["Rating"].str.extract(r"(\d+\.\d+)").astype(float).fillna(0)


    # df["Reviews"] = df["Reviews"].str.extract(r"(\d+[,\d]*)")
    df["Reviews"] = df["Reviews"].str.strip("()")

    df["Stock"] = df["Stock"].str.replace("- order soon.", "", regex=False).str.strip()

    df = df.fillna({
        "Name": "Unknown",
        "Reviews": "Unknown",
        "Stock": "Unknown",
        "Link": "Unknown",
        "Image": "Unknown"
    })

    df = df.sort_values(by="Price", ascending=False).reset_index(drop=True)
    return df


def save_data(df):
    df.to_csv("amazon_products.csv", encoding="utf-8", index=False)
    df.to_excel("amazon_products.xlsx", index=False)


def main():
    keyword = input("Enter product name (default: laptops): ") or "laptops"
    pages = input("Enter number of pages (default: 5): ")
    max_pages = int(pages) if pages.isdigit() else 5

    df = data_frame(keyword, max_pages)
    df = clean_data(df)
    save_data(df)
    print(df)


if __name__ == "__main__":
    main()