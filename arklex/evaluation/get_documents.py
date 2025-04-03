import os
import sys
import json
import pickle
from pathlib import Path
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from arklex.utils.loader import Loader, CrawledURLObject

def get_domain_info(documents):
    summary = None
    for doc in documents:
        if doc['URL'] == 'summary':
            summary = doc['content']
            break
    return summary

def load_docs(documents_dir, config, num_docs=None):
    """
    Load documents from the specified directory.
    
    Args:
        documents_dir (str): Directory containing the documents
        config (dict): Configuration dictionary
        num_docs (int): Number of documents to load
        
    Returns:
        list: List of documents
    """
    rag_docs = config.get("rag_docs", {})
    
    # Handle different formats of rag_docs
    if isinstance(rag_docs, dict):
        # If rag_docs is a dictionary with nested dictionaries (like in research_assistant_config.json)
        total_num_docs = 0
        for doc_name, doc in rag_docs.items():
            if isinstance(doc, dict):
                total_num_docs += doc.get("num", 1)
            else:
                total_num_docs += 1
    elif isinstance(rag_docs, list):
        # If rag_docs is a list of dictionaries
        total_num_docs = sum([doc.get("num") if doc.get("num") else 1 for doc in rag_docs])
    else:
        total_num_docs = 0
    
    filename = "documents.pkl"
    if documents_dir is not None:
        filepath = os.path.join(documents_dir, filename)
        loader = Loader()
        if Path(filepath).exists():
            docs = pickle.load(open(os.path.join(documents_dir, filename), "rb"))
        else:
            docs = []
            # Handle different formats of rag_docs for document loading
            if isinstance(rag_docs, dict):
                # If rag_docs is a dictionary with nested dictionaries
                for doc_name, doc in rag_docs.items():
                    if isinstance(doc, dict):
                        source = doc.get("source")
                        num_docs_for_source = doc.get("num", 1)
                    else:
                        source = doc  # Assume doc is a string URL
                        num_docs_for_source = 1
                    
                    if source:
                        urls = loader.get_all_urls(source, num_docs_for_source)
                        crawled_urls = loader.to_crawled_obj(urls)
                        docs.extend(crawled_urls)
            else:
                # Original code for list format
                for doc in rag_docs:
                    if isinstance(doc, dict):
                        source = doc.get("source")
                        num_docs_for_source = doc.get("num", 1)
                    else:
                        source = doc  # Assume doc is a string URL
                        num_docs_for_source = 1
                    
                    if source:
                        urls = loader.get_all_urls(source, num_docs_for_source)
                        crawled_urls = loader.to_crawled_obj(urls)
                        docs.extend(crawled_urls)
            
            Loader.save(filepath, docs)
        
        if total_num_docs > 50:
            limit = total_num_docs // 5
        else:
            limit = 10
        
        if docs and isinstance(docs[0], CrawledURLObject):
            documents = loader.get_candidates_websites(docs, limit)
        else:
            documents = []
            for doc in docs:
                documents.append({"url": "", "content": doc.page_content, "metadata": doc.metadata})  
    else:
        documents = ""
    
    return documents

if __name__ == "__main__":
    doc_config = json.load(open('./temp_files/richtech_config.json'))
    docs = load_docs('./temp_files', doc_config, 10)