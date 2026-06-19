import json
import os
import requests

from bs4 import BeautifulSoup
from crewai.tools import BaseTool


# =========================================================
# INTERNET SEARCH TOOL
# =========================================================

class SearchInternetTool(BaseTool):

    name: str = "Search the Internet"

    description: str = """
    Searches the internet for information about a topic.

    Input should be a search query string.

    Returns:
    - article titles
    - links
    - snippets
    """

    def _run(self, query: str) -> str:

        try:
            api_key = os.getenv("SERPER_API_KEY")

            if not api_key:
                return "Error: SERPER_API_KEY not found in environment variables."

            url = "https://google.serper.dev/search"

            payload = json.dumps({
                "q": query
            })

            headers = {
                "X-API-KEY": api_key,
                "content-type": "application/json"
            }

            response = requests.post(
                url,
                headers=headers,
                data=payload
            )

            if response.status_code != 200:
                return f"""
Search request failed.

Status Code: {response.status_code}
Response: {response.text}
"""

            results = response.json()

            if "organic" not in results:
                return "No organic search results found."

            organic_results = results["organic"]

            top_result_to_return = 4

            formatted_results = []

            for result in organic_results[:top_result_to_return]:

                try:

                    formatted_results.append(
                        "\n".join([
                            f"Title: {result.get('title', 'N/A')}",
                            f"Link: {result.get('link', 'N/A')}",
                            f"Snippet: {result.get('snippet', 'N/A')}",
                            "---------------------------"
                        ])
                    )

                except Exception:
                    continue

            return "\n".join(formatted_results)

        except Exception as e:
            return f"Error searching the internet: {str(e)}"


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

            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                return f"""
Could not access website.

Status Code: {response.status_code}
"""

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            # Remove noisy tags
            for tag in soup([
                "script",
                "style",
                "nav",
                "footer",
                "header"
            ]):
                tag.decompose()

            text = soup.get_text(separator="\n")

            lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            clean_text = "\n".join(lines)

            max_chars = 5000

            if len(clean_text) > max_chars:

                clean_text = (
                    clean_text[:max_chars]
                    + "\n\n[Content truncated...]"
                )

            return clean_text

        except Exception as e:
            return f"Error scraping website: {str(e)}"