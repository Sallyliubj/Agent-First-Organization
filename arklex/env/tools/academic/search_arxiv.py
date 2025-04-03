from arklex.env.tools.tools import register_tool
import requests
import xml.etree.ElementTree as ET
import json

desc = "Search for academic papers on ArXiv based on a query"
slots = [
    {
        "name": "query",
        "type": "string",
        "description": "The search query for finding relevant papers",
        "prompt": "What topic would you like to search for on ArXiv?",
        "required": True
    },
    {
        "name": "max_results",
        "type": "integer",
        "description": "Maximum number of results to return (default: 5)",
        "prompt": "How many results would you like to see?",
        "required": False
    }
]
outputs = [
    {
        "name": "results",
        "type": "list",
        "description": "A list of papers with their title, authors, abstract, and URL"
    }
]

@register_tool(desc, slots, outputs)
def search_arxiv(query, max_results=5):
    """
    Search ArXiv for academic papers based on a query.
    
    Args:
        query (str): The search query
        max_results (int): Maximum number of results to return
        
    Returns:
        list: A list of dictionaries containing paper information
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        # Define namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip()
            
            # Get authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns).text.strip()
                authors.append(name)
            
            # Get abstract
            abstract = entry.find("atom:summary", ns).text.strip()
            
            # Get URL
            url = entry.find("atom:id", ns).text.strip()
            
            # Get publication date
            published = entry.find("atom:published", ns).text.strip()
            
            results.append({
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "url": url,
                "published": published,
                "source": "ArXiv"
            })
        
        return results
    
    except Exception as e:
        return {"error": f"Error searching ArXiv: {str(e)}"} 