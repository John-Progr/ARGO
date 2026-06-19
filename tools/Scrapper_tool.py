import json
import os
import requests

from bs4 import BeautifulSoup
from crewai.tools import BaseTool


# =========================================================
# WEBSITE SCRAPER TOOL
# =========================================================


class ScrapeWebsiteTool(BaseTool):

    name: str = "Scrape Website Content"

    description: str = """
    Scrapes the content of a website from a URL.
    Input should be a valid URL.
    Returns cleaned article/content text.
    """

    def _run(self, url: str) -> str:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                )
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return f"Could not access website. Status Code: {response.status_code}"

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            if len(clean_text) > 5000:
                clean_text = clean_text[:5000] + "\n\n[Content truncated...]"

            return clean_text

        except Exception as e:
            return f"Error scraping website: {str(e)}"