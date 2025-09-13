import requests
import xml.etree.ElementTree as ET
from langchain.tools import tool

# This is research_papers tool used arXiv


@tool("research_papers", return_direct=True)
def research_papers(query: str) -> str:
    """
    Search academic papers related to a query using the arXiv API.
    Returns top 3 papers with title, authors, and URL.
    """
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": 3
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        entries = root.findall("atom:entry", ns)
        if not entries:
            return f"No academic papers found for: {query}"

        papers = []
        for entry in entries:
            title = entry.find("atom:title", ns).text.strip()
            link = entry.find("atom:id", ns).text.strip()
            authors = [author.find(
                "atom:name", ns).text for author
                       in entry.findall("atom:author", ns)]
            authors_str = ", ".join(authors)
            papers.append(f"- {title} by {authors_str} ({link})")

        return "\n".join(papers)

    except Exception as e:
        return f"Error while fetching research papers: {str(e)}"
