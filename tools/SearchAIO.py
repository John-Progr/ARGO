import json
import os
import requests

from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from dotenv import load_dotenv
load_dotenv()  # Must be called before the tool runs

class SearchAndScrapeTool(BaseTool):

    name: str = "Search and Read Web Content"

    description: str = """
    Searches the internet for a topic and returns the full content
    of the top results — not just snippets.

    Use this whenever you need detailed, up-to-date information
    from the web. Input should be a search query string.

    Returns full article text from the top matching pages.
    """

    top_results: int = 3
    max_chars_per_page: int = 5000

    def _run(self, query: str) -> str:

        # ── Step 1: Search ────────────────────────────────────────────
        links = self._search(query)

        if not links:
            return "Search returned results but none had valid URLs."

        # ── Step 2: Scrape each link ──────────────────────────────────
        output_parts = []

        for i, (title, url) in enumerate(links, start=1):

            content = self._scrape(url)

            output_parts.append(
                "\n".join([
                    f"### Result {i}: {title}",
                    f"URL: {url}",
                    "",
                    content,
                    "",
                    "---",
                ])
            )

        return "\n\n".join(output_parts)

    # ── Helpers ───────────────────────────────────────────────────────

    def _search(self, query: str) -> list[tuple[str, str]]:
        """Returns a list of (title, url) tuples from Serper."""

        api_key = os.getenv("SERPER_API_KEY")

        if not api_key:
            raise EnvironmentError("SERPER_API_KEY not set.")

        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            data=json.dumps({"q": query}),
            timeout=10,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Serper API error {response.status_code}: {response.text}"
            )

        body = response.json()

        if "organic" not in body:
            raise RuntimeError(
                f"Serper response has no 'organic' key. Full response: {body}"
            )

        results = body["organic"]

        return [
            (r.get("title", "Untitled"), r.get("link", ""))
            for r in results[: self.top_results]
            if r.get("link")
        ]

    def _scrape(self, url: str) -> str:
        """Returns cleaned text from a URL."""

        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36"
                    )
                },
                timeout=10,
            )

            if response.status_code != 200:
                return f"[Could not load page: HTTP {response.status_code}]"

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            lines = [
                line.strip()
                for line in soup.get_text(separator="\n").splitlines()
                if line.strip()
            ]

            text = "\n".join(lines)

            if len(text) > self.max_chars_per_page:
                text = text[: self.max_chars_per_page] + "\n\n[Truncated...]"

            return text

        except Exception as e:
            return f"[Scrape error: {e}]"