from langchain.tools import tool
import requests
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import re

load_dotenv()

_tavily_client = None


def get_tavily_client() -> TavilyClient:
    """Lazily initializes and returns the TavilyClient instance."""
    global _tavily_client
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not configured in the environment.")
    if _tavily_client is None:
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    if not query or not query.strip():
        return "Error: Search query cannot be empty."

    try:
        client = get_tavily_client()
        results = client.search(query=query.strip(), max_results=5)
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Tavily search failed: {str(e)}"

    out = []
    items = results.get("results", []) if isinstance(results, dict) else []

    if not items:
        return f"No search results found for: {query}"

    for r in items:
        title = r.get("title", "No Title")
        url = r.get("url", "")
        content = r.get("content", "")[:300]
        out.append(
            f"Title: {title}\nURL: {url}\nSnippet: {content}\n"
        )

    return "\n----\n".join(out)


@tool
def scrape_url(url: str) -> str:
    """
    Scrape and extract clean readable content from a URL.
    Uses multiple extraction strategies for better reliability.
    """
    if not url or not isinstance(url, str) or not url.strip().startswith(("http://", "https://")):
        return "Error: A valid HTTP or HTTPS URL must be provided for scraping."

    url = url.strip()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    try:
        # ── Fetch page ─────────────────────────────────────
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        if response.status_code in (401, 403):
            return f"Access denied (HTTP {response.status_code}) while attempting to scrape: {url}"
        if response.status_code == 404:
            return f"Page not found (HTTP 404): {url}"

        response.raise_for_status()

        html = response.text
        if not html or not html.strip():
            return "The fetched page was empty."

        # ──────────────────────────────────────────────────
        # Strategy 1 → trafilatura (BEST for articles/blogs)
        # ──────────────────────────────────────────────────
        try:
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False
            )

            if extracted and len(extracted.strip()) > 200:
                cleaned = re.sub(r'\s+', ' ', extracted)
                return cleaned[:5000]
        except Exception:
            pass

        # ──────────────────────────────────────────────────
        # Strategy 2 → readability
        # ──────────────────────────────────────────────────
        try:
            doc = Document(html)
            clean_html = doc.summary()

            soup = BeautifulSoup(clean_html, "html.parser")

            for tag in soup([
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "aside",
                "form"
            ]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)

            if text and len(text.strip()) > 200:
                cleaned = re.sub(r'\s+', ' ', text)
                return cleaned[:5000]
        except Exception:
            pass

        # ──────────────────────────────────────────────────
        # Strategy 3 → fallback full page extraction
        # ──────────────────────────────────────────────────
        try:
            soup = BeautifulSoup(html, "html.parser")

            for tag in soup([
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "aside",
                "form"
            ]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)

            cleaned = re.sub(r'\s+', ' ', text)

            if cleaned and len(cleaned.strip()) > 0:
                return cleaned[:5000]
        except Exception:
            pass

        return "Could not extract meaningful content from the page."

    except requests.exceptions.Timeout:
        return "Request timed out while scraping the URL."

    except requests.exceptions.ConnectionError:
        return "Connection failed: Unable to reach the server at the requested URL."

    except requests.exceptions.HTTPError as e:
        return f"HTTP error occurred: {str(e)}"

    except requests.exceptions.RequestException as e:
        return f"Network error while scraping URL: {str(e)}"

    except Exception as e:
        return f"Could not scrape URL: {str(e)}"