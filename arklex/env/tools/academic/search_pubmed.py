from arklex.env.tools.tools import register_tool
import requests
import json
import xml.etree.ElementTree as ET

desc = "Search for academic papers on PubMed based on a query"
slots = [
    {
        "name": "query",
        "type": "string",
        "description": "The search query for finding relevant papers",
        "prompt": "What topic would you like to search for on PubMed?",
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
def search_pubmed(query, max_results=5):
    """
    Search PubMed for academic papers based on a query.
    
    Args:
        query (str): The search query
        max_results (int): Maximum number of results to return
        
    Returns:
        list: A list of dictionaries containing paper information
    """
    # PubMed API endpoints
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    try:
        # First, search for IDs matching the query
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results
        }
        
        search_response = requests.get(esearch_url, params=search_params)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        # Get the IDs from the search results
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not ids:
            return []
        
        # Fetch detailed information for each ID
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml"
        }
        
        fetch_response = requests.get(efetch_url, params=fetch_params)
        fetch_response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(fetch_response.content)
        
        results = []
        for article in root.findall(".//PubmedArticle"):
            try:
                # Extract title
                title_element = article.find(".//ArticleTitle")
                title = title_element.text if title_element is not None else "No title available"
                
                # Extract authors
                authors = []
                author_list = article.findall(".//Author")
                for author in author_list:
                    last_name = author.find("LastName")
                    fore_name = author.find("ForeName")
                    
                    if last_name is not None and fore_name is not None:
                        authors.append(f"{fore_name.text} {last_name.text}")
                    elif last_name is not None:
                        authors.append(last_name.text)
                
                # Extract abstract
                abstract_elements = article.findall(".//AbstractText")
                abstract = " ".join([elem.text for elem in abstract_elements if elem.text]) if abstract_elements else "No abstract available"
                
                # Extract PMID for URL
                pmid_element = article.find(".//PMID")
                pmid = pmid_element.text if pmid_element is not None else ""
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
                
                # Extract publication date
                pub_date = article.find(".//PubDate")
                year = pub_date.find("Year")
                month = pub_date.find("Month")
                day = pub_date.find("Day")
                
                published = ""
                if year is not None:
                    published = year.text
                    if month is not None:
                        published = f"{month.text} {published}"
                        if day is not None:
                            published = f"{day.text} {published}"
                
                results.append({
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "url": url,
                    "published": published,
                    "source": "PubMed"
                })
            except Exception as e:
                # Skip this article if there's an error parsing it
                continue
        
        return results
    
    except Exception as e:
        return {"error": f"Error searching PubMed: {str(e)}"} 