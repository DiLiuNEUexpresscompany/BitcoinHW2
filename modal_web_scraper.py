import os
import json
import datetime
import modal
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Create Modal app
app = modal.App(name="Di-Liu-Github-daily-trending-scraper")

# Create Volume
VOLUME_NAME = "github-trending-volume"
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

# Custom container image
crawler_image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "crawl4ai", "playwright"
).run_commands(
    "playwright install-deps chromium",
    "playwright install chromium",
    "crawl4ai-setup"
)

# CSS extraction strategy
TRENDING_SCHEMA = {
    "name": "GitHub Trending Repos",
    "baseSelector": "article.Box-row",
    "fields": [
        {"name": "repo_name", "selector": "h2 a", "type": "text"},
        {"name": "repo_link", "selector": "h2 a", "type": "attribute", "attribute": "href"},
        {"name": "description", "selector": "p", "type": "text"},
        {"name": "language", "selector": "[itemprop='programmingLanguage']", "type": "text"},
        {"name": "stars", "selector": "a[href$='/stargazers']", "type": "text"},
    ],
}

@app.function(image=crawler_image, volumes={"/data": volume})
async def scrape_github_trending():
    """Scrape GitHub Trending page and store to Volume"""
    print("🚀 Starting GitHub Trending Scraper...")

    # Configure browser and crawler
    browser_config = BrowserConfig(headless=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(TRENDING_SCHEMA),
    )

    # Execute scraping
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://github.com/trending?since=daily", config=crawler_config)
        trending_repos = json.loads(result.extracted_content)

    # Post-processing: generate full links and print logs
    print("\n📦 Scraped repositories:")
    for repo in trending_repos:
        # Fix link format
        repo_name_clean = repo["repo_name"].split("/")[-1].strip()  # Extract clean repository name
        repo["full_repo_link"] = f"https://github.com/{repo['repo_link'].lstrip('/')}"

        # Print formatted log
        print(f"✅ {repo_name_clean.ljust(25)} | Stars: {repo['stars'].rjust(8)}")

        # Clean original data format
        repo["repo_link"] = repo["repo_link"].strip()

    print(f"\n🎉 Total {len(trending_repos)} repositories scraped!")

    # Save data to Volume
    today_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    file_path = f"/data/github_trending_{today_date}.json"

    data = {
        "time": today_date,
        "repos": trending_repos
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    volume.commit()
    print(f"\n💾 Saved trending data to: {file_path}")
    return file_path

@app.function(image=crawler_image, schedule=modal.Period(days=1), volumes={"/data": volume})
def daily_scrape():
    """Automatically scrape GitHub Trending daily"""
    json_file_path = scrape_github_trending.remote()
    print(f"✅ Daily GitHub Trending scrape complete. Data saved to: {json_file_path}")

@app.function(image=crawler_image, volumes={"/data": volume})
def list_stored_data():
    """List stored files"""
    files = os.listdir("/data")
    print("📂 Stored files in Volume:", files)
    return files

@app.local_entrypoint()
def main():
    """Local debug entry point"""
    json_file_path = scrape_github_trending.remote()
    print(f"✅ Scraped data saved at: {json_file_path}")
    stored_files = list_stored_data.remote()
    print(f"📂 Stored JSON files: {stored_files}")

if __name__ == "__main__":
    main()