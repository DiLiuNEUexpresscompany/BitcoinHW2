import modal
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import datetime
import json

# Create Modal app
app = modal.App(name="Di-Liu-Github-daily-trending-api")

# Custom container image
crawler_image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "crawl4ai", 
    "playwright",
    "fastapi[standard]"  # Add FastAPI dependency
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

@app.function(image=crawler_image)
@modal.web_endpoint(method="GET", docs=True)
async def get_trending():
    """API endpoint to get real-time GitHub Trending data"""
    print("🚀 Processing GitHub Trending request...")

    # Configure browser and crawler
    browser_config = BrowserConfig(headless=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(TRENDING_SCHEMA),
    )

    # Execute scraping
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://github.com/trending?since=daily", 
            config=crawler_config
        )
        trending_repos = json.loads(result.extracted_content)

    # Post-processing
    for repo in trending_repos:
        repo["full_repo_link"] = f"https://github.com/{repo['repo_link'].lstrip('/')}"
        repo["repo_name"] = repo["repo_name"].strip()
        repo["repo_link"] = repo["repo_link"].strip()

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "count": len(trending_repos),
        "repositories": trending_repos
    }

@app.function(image=crawler_image)
@modal.web_endpoint(method="GET", docs=True)
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.local_entrypoint()
def main():
    """Local debug entry point"""
    print("👉 Local test: Use modal serve to deploy and access endpoint URL")

if __name__ == "__main__":
    main()