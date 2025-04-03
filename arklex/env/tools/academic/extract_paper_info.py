from arklex.env.tools.tools import register_tool
import requests
from bs4 import BeautifulSoup
import re

desc = "Extract detailed information from a research paper URL"
slots = [
    {
        "name": "url",
        "type": "string",
        "description": "The URL of the research paper to extract information from",
        "prompt": "Please provide the URL of the research paper you want to analyze:",
        "required": True
    },
    {
        "name": "source",
        "type": "string",
        "description": "The source of the paper (ArXiv, PubMed, etc.)",
        "prompt": "What is the source of this paper (ArXiv, PubMed, etc.)?",
        "required": False
    }
]
outputs = [
    {
        "name": "paper_info",
        "type": "dict",
        "description": "Detailed information about the paper including title, authors, abstract, methodology, results, and conclusions"
    }
]

@register_tool(desc, slots, outputs)
def extract_paper_info(url, source=""):
    """
    Extract detailed information from a research paper URL.
    
    Args:
        url (str): The URL of the research paper
        source (str): The source of the paper (ArXiv, PubMed, etc.)
        
    Returns:
        dict: A dictionary containing detailed information about the paper
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize result dictionary
        result = {
            "title": "",
            "authors": [],
            "abstract": "",
            "methodology": "",
            "results": "",
            "conclusions": "",
            "references": [],
            "url": url,
            "source": source
        }
        
        # Extract information based on the source
        if "arxiv.org" in url:
            # ArXiv paper extraction
            result["title"] = soup.find("h1", class_="title").text.replace("Title:", "").strip() if soup.find("h1", class_="title") else ""
            
            authors_div = soup.find("div", class_="authors")
            if authors_div:
                result["authors"] = [author.strip() for author in authors_div.text.replace("Authors:", "").split(",")]
            
            abstract_div = soup.find("blockquote", class_="abstract")
            if abstract_div:
                result["abstract"] = abstract_div.text.replace("Abstract:", "").strip()
            
            # For ArXiv, we might not have structured sections, so we'll try to extract the PDF
            pdf_link = soup.find("a", title="Download PDF")
            if pdf_link:
                result["pdf_url"] = "https://arxiv.org" + pdf_link["href"] if pdf_link["href"].startswith("/") else pdf_link["href"]
            
        elif "pubmed.ncbi.nlm.nih.gov" in url:
            # PubMed paper extraction
            result["title"] = soup.find("h1", class_="heading-title").text.strip() if soup.find("h1", class_="heading-title") else ""
            
            authors_div = soup.find("div", class_="authors-list")
            if authors_div:
                author_links = authors_div.find_all("a", class_="full-name")
                result["authors"] = [author.text.strip() for author in author_links]
            
            abstract_div = soup.find("div", class_="abstract-content")
            if abstract_div:
                result["abstract"] = abstract_div.text.strip()
            
            # Try to find sections like methods, results, conclusions
            sections = soup.find_all("div", class_="abstract-section")
            for section in sections:
                label = section.find("label")
                if label:
                    section_name = label.text.strip().lower()
                    section_text = section.find("p").text.strip() if section.find("p") else ""
                    
                    if "method" in section_name:
                        result["methodology"] = section_text
                    elif "result" in section_name:
                        result["results"] = section_text
                    elif "conclusion" in section_name:
                        result["conclusions"] = section_text
        
        else:
            # Generic extraction for other sources
            # Title is usually in the first h1 tag
            title_tag = soup.find("h1")
            if title_tag:
                result["title"] = title_tag.text.strip()
            
            # Try to find abstract
            abstract_section = soup.find(["div", "section"], string=re.compile("abstract", re.IGNORECASE))
            if abstract_section:
                next_p = abstract_section.find_next("p")
                if next_p:
                    result["abstract"] = next_p.text.strip()
            
            # Try to find methodology/methods
            methods_section = soup.find(["div", "section", "h2", "h3"], string=re.compile("method|methodology", re.IGNORECASE))
            if methods_section:
                method_text = []
                for p in methods_section.find_next_siblings("p"):
                    if p.find(["h2", "h3"]):  # Stop if we hit another heading
                        break
                    method_text.append(p.text.strip())
                result["methodology"] = " ".join(method_text)
            
            # Try to find results
            results_section = soup.find(["div", "section", "h2", "h3"], string=re.compile("result", re.IGNORECASE))
            if results_section:
                result_text = []
                for p in results_section.find_next_siblings("p"):
                    if p.find(["h2", "h3"]):  # Stop if we hit another heading
                        break
                    result_text.append(p.text.strip())
                result["results"] = " ".join(result_text)
            
            # Try to find conclusions
            conclusion_section = soup.find(["div", "section", "h2", "h3"], string=re.compile("conclusion", re.IGNORECASE))
            if conclusion_section:
                conclusion_text = []
                for p in conclusion_section.find_next_siblings("p"):
                    if p.find(["h2", "h3"]):  # Stop if we hit another heading
                        break
                    conclusion_text.append(p.text.strip())
                result["conclusions"] = " ".join(conclusion_text)
        
        # Clean up empty fields
        for key in list(result.keys()):
            if not result[key] and key not in ["url", "source"]:
                if isinstance(result[key], list):
                    result[key] = []
                else:
                    result[key] = "Information not available"
        
        return result
    
    except Exception as e:
        return {"error": f"Error extracting paper information: {str(e)}", "url": url} 