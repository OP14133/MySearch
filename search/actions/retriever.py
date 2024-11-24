from typing import List, Type
from MySearch.search.config import Config

def get_retriever(retriever):
    """
    Gets the retriever
    Args:
        retriever: retriever name

    Returns:
        retriever: Retriever class

    """
    match retriever:
        case "google":
            from MySearch.search.retrievers import GoogleSearch

            retriever = GoogleSearch
        case "searx":
            from MySearch.search.retrievers import SearxSearch

            retriever = SearxSearch
        case "searchapi":
            from MySearch.search.retrievers import SearchApiSearch

            retriever = SearchApiSearch
        case "serpapi":
            from MySearch.search.retrievers import SerpApiSearch

            retriever = SerpApiSearch
        case "serper":
            from MySearch.search.retrievers import SerperSearch

            retriever = SerperSearch
        case "duckduckgo":
            from MySearch.search.retrievers import Duckduckgo

            retriever = Duckduckgo
        case "bing":
            from MySearch.search.retrievers import BingSearch

            retriever = BingSearch
        case "arxiv":
            from MySearch.search.retrievers import ArxivSearch

            retriever = ArxivSearch
        case "tavily":
            from MySearch.search.retrievers import TavilySearch

            retriever = TavilySearch
        case "exa":
            from MySearch.search.retrievers import ExaSearch

            retriever = ExaSearch
        case "semantic_scholar":
            from MySearch.search.retrievers import SemanticScholarSearch

            retriever = SemanticScholarSearch
        case "pubmed_central":
            from MySearch.search.retrievers import PubMedCentralSearch

            retriever = PubMedCentralSearch
        case "custom":
            from MySearch.search.retrievers import CustomRetriever

            retriever = CustomRetriever

        case _:
            retriever = None

    return retriever


def get_retrievers(headers, cfg):
    """
    Determine which retriever(s) to use based on headers, config, or default.

    Args:
        headers (dict): The headers dictionary
        cfg (Config): The configuration object

    Returns:
        list: A list of retriever classes to be used for searching.
    """
    # Check headers first for multiple retrievers
    if headers.get("retrievers"):
        retrievers = headers.get("retrievers").split(",")
    # If not found, check headers for a single retriever
    elif headers.get("retriever"):
        retrievers = [headers.get("retriever")]
    # If not in headers, check config for multiple retrievers
    elif cfg.retrievers:
        retrievers = cfg.retrievers
    # If not found, check config for a single retriever
    elif cfg.retriever:
        retrievers = [cfg.retriever]
    # If still not set, use default retriever
    else:
        retrievers = [get_default_retriever().__name__]

    # Convert retriever names to actual retriever classes
    # Use get_default_retriever() as a fallback for any invalid retriever names
    return [get_retriever(r) or get_default_retriever() for r in retrievers]


def get_default_retriever(retriever):
    from MySearch.search.retrievers import TavilySearch

    return TavilySearch