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


from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def validate_url(url: str) -> bool:
    """Validates that a URL is a syntactically valid HTTP or HTTPS URL with a network location."""
    if not url or not isinstance(url, str):
        return False
    clean = url.strip()
    if not clean.startswith(("http://", "https://")):
        return False
    try:
        parsed = urlparse(clean)
        return bool(parsed.scheme in ("http", "https") and parsed.netloc)
    except Exception:
        return False


def canonicalize_url(url: str) -> str:
    """
    Normalizes a URL by stripping tracking parameters, normalizing scheme/netloc to lowercase,
    and trimming trailing slashes on non-root paths.
    """
    if not validate_url(url):
        return url.strip() if isinstance(url, str) else ""
    try:
        parsed = urlparse(url.strip())
        tracking_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "gclid", "fbclid", "ref", "source"
        }
        filtered_query = [
            (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in tracking_params
        ]
        new_query = urlencode(filtered_query)
        path = parsed.path
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        canonical = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            new_query,
            ""  # Strip fragment anchor
        ))
        return canonical
    except Exception:
        return url.strip()


def tavily_search_structured(query: str, max_results: int = 5) -> list[dict]:
    """
    Executes search via Tavily and returns a structured, deduplicated list of verified sources:
    [{"title": str, "url": str, "snippet": str, "query": str}, ...]
    """
    if not query or not isinstance(query, str) or not query.strip():
        return []

    clean_query = query.strip()
    client = get_tavily_client()
    results = client.search(query=clean_query, max_results=max_results)

    items = results.get("results", []) if isinstance(results, dict) else []
    structured_sources = []
    seen_urls = set()

    for item in items:
        raw_url = item.get("url", "")
        if not validate_url(raw_url):
            continue
        canon_url = canonicalize_url(raw_url)
        if canon_url in seen_urls:
            continue
        seen_urls.add(canon_url)

        title = str(item.get("title") or "Untitled Source").strip()
        raw_snippet = str(item.get("content") or "").strip()
        snippet = re.sub(r'\s+', ' ', raw_snippet)[:500]

        structured_sources.append({
            "title": title,
            "url": canon_url,
            "snippet": snippet,
            "query": clean_query,
            "status": "discovered"
        })

    return structured_sources


def extract_sources_from_text(text: str) -> list[dict]:
    """Extracts structured source information from search text blocks, markdown links, or URLs."""
    if not text or not isinstance(text, str):
        return []

    sources = []
    seen_urls = set()

    # Pattern 1: Title: ... \n URL: ... (\n Snippet: ...)
    block_pattern1 = re.compile(
        r"Title:\s*(?P<title>[^\n]+)\s*\n(?:URL|Source):\s*(?P<url>https?://[^\s\n]+)(?:\s*\nSnippet:\s*(?P<snippet>[^\n]+))?",
        re.IGNORECASE
    )
    for m in block_pattern1.finditer(text):
        u = m.group("url").strip()
        if validate_url(u):
            canon = canonicalize_url(u)
            if canon not in seen_urls:
                seen_urls.add(canon)
                sources.append({
                    "title": m.group("title").strip(),
                    "url": canon,
                    "snippet": (m.group("snippet") or "").strip(),
                    "status": "discovered"
                })

    # Pattern 2: Source: https://... \n Title: ...
    block_pattern2 = re.compile(
        r"(?:URL|Source):\s*(?P<url>https?://[^\s\n]+)\s*\nTitle:\s*(?P<title>[^\n]+)(?:\s*\nSnippet:\s*(?P<snippet>[^\n]+))?",
        re.IGNORECASE
    )
    for m in block_pattern2.finditer(text):
        u = m.group("url").strip()
        if validate_url(u):
            canon = canonicalize_url(u)
            if canon not in seen_urls:
                seen_urls.add(canon)
                sources.append({
                    "title": m.group("title").strip(),
                    "url": canon,
                    "snippet": (m.group("snippet") or "").strip(),
                    "status": "discovered"
                })

    # Pattern 3: Markdown links [Title](https://...)
    md_pattern = re.compile(r"\[(?P<title>[^\]\n]+)\]\((?P<url>https?://[^\s\)]+)\)")
    for m in md_pattern.finditer(text):
        u = m.group("url").strip()
        if validate_url(u):
            canon = canonicalize_url(u)
            if canon not in seen_urls:
                seen_urls.add(canon)
                sources.append({
                    "title": m.group("title").strip(),
                    "url": canon,
                    "snippet": "",
                    "status": "discovered"
                })

    # Pattern 4: Fallback to any raw URLs if no structured blocks found
    if not sources:
        raw_url_pattern = re.compile(r"https?://[^\s\"'>,\)]+")
        for raw_u in raw_url_pattern.findall(text):
            cleaned_u = raw_u.rstrip(".,;)]")
            if validate_url(cleaned_u):
                canon = canonicalize_url(cleaned_u)
                if canon not in seen_urls:
                    seen_urls.add(canon)
                    sources.append({
                        "title": f"Source: {canon}",
                        "url": canon,
                        "snippet": "",
                        "status": "discovered"
                    })

    return sources


def scrape_url_structured(url: str, title: str = "", timeout: int = 15) -> dict:
    """
    Executes scraping on a URL and returns a structured result dictionary:
    {"url": url, "title": title, "content": text, "text": text, "status": "scraped" | "failed", "error": error}
    """
    if not validate_url(url):
        return {
            "url": url,
            "title": title or "Invalid URL",
            "content": "",
            "text": "",
            "status": "failed",
            "error": "Invalid HTTP/HTTPS URL."
        }

    canon_url = canonicalize_url(url)
    res = scrape_url.invoke({"url": canon_url})

    is_error = any(res.startswith(prefix) for prefix in (
        "Error:", "Access denied", "Page not found", "Could not extract",
        "Request timed out", "Connection failed", "HTTP error", "Network error", "Could not scrape"
    ))

    if is_error:
        return {
            "url": canon_url,
            "title": title or canon_url,
            "content": "",
            "text": "",
            "status": "failed",
            "error": res
        }

    return {
        "url": canon_url,
        "title": title or canon_url,
        "content": res,
        "text": res,
        "status": "scraped",
        "error": None
    }


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    if not query or not query.strip():
        return "Error: Search query cannot be empty."

    try:
        sources = tavily_search_structured(query, max_results=5)
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Tavily search failed: {str(e)}"

    if not sources:
        return f"No search results found for: {query}"

    out = []
    for s in sources:
        out.append(
            f"Title: {s['title']}\nURL: {s['url']}\nSnippet: {s['snippet']}\n"
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