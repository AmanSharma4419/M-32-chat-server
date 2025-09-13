import requests
from langchain.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# This is web search tool used SerpAPI


@tool("web_search", return_direct=False)
def web_search(query: str) -> str:
    """
    Perform a Google search via SerpAPI and return top 3 results.
    """
    if not SERPAPI_API_KEY:
        return "SerpAPI API key not configured."

    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": 3
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("organic_results", [])[:3]:
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })

        if not results:
            return "No search results found."

        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"{i}. {result['title']}\n"
                f"   URL: {result['link']}\n"
                f"   Snippet: {result['snippet']}\n"
            )

        return "\n".join(formatted_results)

    except Exception as e:
        return f"Search error: {str(e)}"
