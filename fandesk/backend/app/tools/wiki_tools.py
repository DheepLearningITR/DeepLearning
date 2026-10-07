"""Cinema Buff's tools over the Wikipedia API (free, no key).

Wikimedia's API policy requires a descriptive User-Agent. Lookups are cached
in memory for 24 hours. Page text is returned inside <page> tags and the agent's
prompt tells it to treat that text as data, never as instructions.
"""

import time
from urllib.parse import quote

import httpx

from . import ToolOutput, function_spec

SEARCH_URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
CACHE_TTL_S = 24 * 3600

SPECS = [
    function_spec(
        "search_wikipedia",
        "Search English Wikipedia and return the top matching page titles with a snippet.",
        {"query": {"type": "string", "description": "Search terms, e.g. 'Vikram 2022 film'."}},
        ["query"],
    ),
    function_spec(
        "get_page_summary",
        "Get the lead summary of one Wikipedia page by its exact title.",
        {"title": {"type": "string", "description": "Exact page title from search results."}},
        ["title"],
    ),
]


def _strip_tags(snippet: str) -> str:
    return snippet.replace('<span class="searchmatch">', "").replace("</span>", "").replace("&quot;", '"')


class WikiTools:
    def __init__(self, user_agent: str, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": user_agent, "Accept": "application/json"}, timeout=10.0, follow_redirects=True
        )
        self._cache: dict[str, tuple[float, object]] = {}

    async def _get_json(self, url: str, params: dict | None = None):
        key = url + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
        hit = self._cache.get(key)
        if hit and time.time() - hit[0] < CACHE_TTL_S:
            return hit[1]
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        self._cache[key] = (time.time(), data)
        return data

    async def search_wikipedia(self, args: dict) -> ToolOutput:
        query = str(args.get("query", "")).strip()
        if not query:
            return ToolOutput(text="ERROR: query is empty.", summary="Error: empty query", ok=False)
        try:
            data = await self._get_json(
                SEARCH_URL,
                {"action": "query", "list": "search", "srsearch": query, "srlimit": 5, "format": "json"},
            )
        except httpx.HTTPError as e:
            return ToolOutput(text=f"ERROR: Wikipedia search failed: {e}", summary="Error: search failed", ok=False)
        hits = data.get("query", {}).get("search", [])
        if not hits:
            return ToolOutput(text="No results.", summary="0 results")
        lines = [f"- {h['title']}: {_strip_tags(h.get('snippet', ''))}" for h in hits]
        return ToolOutput(
            text="<search_results>\n" + "\n".join(lines) + "\n</search_results>",
            summary=f"{len(hits)} results",
            extra={"titles": [h["title"] for h in hits]},
        )

    async def get_page_summary(self, args: dict) -> ToolOutput:
        title = str(args.get("title", "")).strip()
        if not title:
            return ToolOutput(text="ERROR: title is empty.", summary="Error: empty title", ok=False)
        try:
            data = await self._get_json(SUMMARY_URL.format(title=quote(title.replace(" ", "_"), safe="")))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return ToolOutput(text=f"No page titled '{title}'.", summary="Page not found", ok=False)
            return ToolOutput(text=f"ERROR: {e}", summary="Error: lookup failed", ok=False)
        except httpx.HTTPError as e:
            return ToolOutput(text=f"ERROR: {e}", summary="Error: lookup failed", ok=False)
        page_title = data.get("title", title)
        extract = data.get("extract", "")
        return ToolOutput(
            text=f'<page title="{page_title}">\n{extract}\n</page>',
            summary=f"{len(extract):,} characters",
            extra={"title": page_title},
        )

    def handlers(self):
        return {"search_wikipedia": self.search_wikipedia, "get_page_summary": self.get_page_summary}

    async def aclose(self):
        await self._client.aclose()
