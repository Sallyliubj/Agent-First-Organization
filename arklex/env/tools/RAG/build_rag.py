import os
import argparse
import pickle
from pathlib import Path
import logging
import json
import requests
from bs4 import BeautifulSoup
import re
import time
from tqdm import tqdm

from arklex.utils.loader import Loader

logger = logging.getLogger(__name__)


def build_rag(output_dir, rag_docs):
    """
    Build RAG documents from the given sources.
    
    Args:
        output_dir (str): The output directory to save the RAG documents
        rag_docs (dict or list): The RAG documents to build
    """
    if not rag_docs:
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Handle both dictionary and list formats
    if isinstance(rag_docs, dict):
        # Dictionary format (like in research_assistant_config.json)
        for doc_name, doc in rag_docs.items():
            # The error is here - doc is expected to be a dictionary but might be a string
            # Let's add a check to handle both cases
            if isinstance(doc, dict):
                source = doc.get("source")
                desc = doc.get("desc", "")
                num = doc.get("num", 1)
            elif isinstance(doc, str):
                # If doc is a string, assume it's the source URL
                source = doc
                desc = ""
                num = 1
            else:
                print(f"Skipping invalid document format for {doc_name}")
                continue
            
            if not source:
                continue
            
            print(f"Building RAG document for {doc_name} from {source}")
            
            try:
                # Fetch the content from the source
                response = requests.get(source)
                response.raise_for_status()
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract the text content
                text = soup.get_text()
                
                # Clean up the text
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Save the text to a file
                output_file = os.path.join(output_dir, f"{doc_name}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                print(f"Saved RAG document to {output_file}")
                
                # If num > 1, fetch additional pages
                if num > 1:
                    # This is a simplified approach - in a real implementation,
                    # you would need to handle pagination properly for each source
                    pass
                    
            except Exception as e:
                print(f"Error building RAG document for {doc_name}: {str(e)}")
    
    elif isinstance(rag_docs, list):
        # List format (like in customer_service_config.json)
        for i, doc in enumerate(rag_docs):
            # Generate a document name if not provided
            doc_name = f"doc_{i+1}"
            
            if isinstance(doc, dict):
                source = doc.get("source")
                desc = doc.get("desc", "")
                num = doc.get("num", 1)
            elif isinstance(doc, str):
                # If doc is a string, assume it's the source URL
                source = doc
                desc = ""
                num = 1
            else:
                print(f"Skipping invalid document format for {doc_name}")
                continue
            
            if not source:
                continue
            
            print(f"Building RAG document for {doc_name} from {source}")
            
            try:
                # Fetch the content from the source
                response = requests.get(source)
                response.raise_for_status()
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract the text content
                text = soup.get_text()
                
                # Clean up the text
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Save the text to a file
                output_file = os.path.join(output_dir, f"{doc_name}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                print(f"Saved RAG document to {output_file}")
                
                # If num > 1, fetch additional pages
                if num > 1:
                    # This is a simplified approach - in a real implementation,
                    # you would need to handle pagination properly for each source
                    pass
                    
            except Exception as e:
                print(f"Error building RAG document for {doc_name}: {str(e)}")
    
    else:
        print(f"Unsupported rag_docs format: {type(rag_docs)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--base_url", required=True, type=str, help="base url to crawl")
    parser.add_argument("--folder_path", required=True, type=str, help="location to save the documents")
    parser.add_argument("--max_num", type=int, default=10, help="maximum number of urls to crawl")
    args = parser.parse_args()

    build_rag(folder_path=args.folder_path, docs=[{"source": args.base_url, "num": args.max_num}])