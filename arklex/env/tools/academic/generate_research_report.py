from arklex.env.tools.tools import register_tool
import json
from datetime import datetime

desc = "Generate a structured research report from multiple paper summaries"
slots = [
    {
        "name": "papers",
        "type": "list",
        "description": "List of paper information dictionaries",
        "prompt": "Please provide the list of papers to include in the report:",
        "required": True
    },
    {
        "name": "research_question",
        "type": "string",
        "description": "The original research question",
        "prompt": "What is the research question you're addressing?",
        "required": True
    },
    {
        "name": "format",
        "type": "string",
        "description": "The format of the report (markdown, json, text)",
        "prompt": "In what format would you like the report (markdown, json, text)?",
        "required": False
    }
]
outputs = [
    {
        "name": "report",
        "type": "string",
        "description": "A structured research report in the specified format"
    }
]

@register_tool(desc, slots, outputs)
def generate_research_report(papers, research_question, format="markdown"):
    """
    Generate a structured research report from multiple paper summaries.
    
    Args:
        papers (list): List of paper information dictionaries
        research_question (str): The original research question
        format (str): The format of the report (markdown, json, text)
        
    Returns:
        str: A structured research report in the specified format
    """
    if not papers:
        return {"error": "No papers provided for the report"}
    
    try:
        # Group papers by themes/topics
        # This is a simplified approach - in a real implementation, 
        # you might use NLP techniques to cluster papers by topic
        sources = {}
        for paper in papers:
            source = paper.get("source", "Unknown")
            if source not in sources:
                sources[source] = []
            sources[source].append(paper)
        
        # Generate report based on format
        if format.lower() == "json":
            report = {
                "research_question": research_question,
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "summary": f"Research report addressing: {research_question}",
                "sources": sources,
                "papers": papers
            }
            return json.dumps(report, indent=2)
        
        elif format.lower() == "text":
            report = f"RESEARCH REPORT\n\n"
            report += f"Research Question: {research_question}\n"
            report += f"Date Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
            
            report += "SUMMARY OF FINDINGS\n\n"
            
            # Add papers by source
            for source, source_papers in sources.items():
                report += f"\n{source.upper()} PAPERS:\n"
                for i, paper in enumerate(source_papers, 1):
                    report += f"\n{i}. {paper.get('title', 'Untitled')}\n"
                    report += f"   Authors: {', '.join(paper.get('authors', ['Unknown']))}\n"
                    report += f"   Abstract: {paper.get('abstract', 'No abstract available')}\n"
                    
                    if paper.get('methodology'):
                        report += f"   Methodology: {paper.get('methodology')}\n"
                    if paper.get('results'):
                        report += f"   Results: {paper.get('results')}\n"
                    if paper.get('conclusions'):
                        report += f"   Conclusions: {paper.get('conclusions')}\n"
                    
                    report += f"   URL: {paper.get('url', 'No URL available')}\n"
            
            report += "\nREFERENCES\n\n"
            for i, paper in enumerate(papers, 1):
                authors = ', '.join(paper.get('authors', ['Unknown']))
                title = paper.get('title', 'Untitled')
                source = paper.get('source', 'Unknown')
                url = paper.get('url', '')
                published = paper.get('published', 'n.d.')
                
                report += f"{i}. {authors}. ({published}). {title}. {source}. {url}\n"
            
            return report
        
        else:  # Default to markdown
            report = f"# Research Report: {research_question}\n\n"
            report += f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n"
            
            report += "## Summary of Findings\n\n"
            
            # Add papers by source
            for source, source_papers in sources.items():
                report += f"\n### {source} Papers\n\n"
                for paper in source_papers:
                    report += f"#### {paper.get('title', 'Untitled')}\n\n"
                    report += f"**Authors:** {', '.join(paper.get('authors', ['Unknown']))}\n\n"
                    report += f"**Abstract:** {paper.get('abstract', 'No abstract available')}\n\n"
                    
                    if paper.get('methodology'):
                        report += f"**Methodology:** {paper.get('methodology')}\n\n"
                    if paper.get('results'):
                        report += f"**Results:** {paper.get('results')}\n\n"
                    if paper.get('conclusions'):
                        report += f"**Conclusions:** {paper.get('conclusions')}\n\n"
                    
                    report += f"**URL:** [{paper.get('url', '#')}]({paper.get('url', '#')})\n\n"
                    report += "---\n\n"
            
            report += "## References\n\n"
            for i, paper in enumerate(papers, 1):
                authors = ', '.join(paper.get('authors', ['Unknown']))
                title = paper.get('title', 'Untitled')
                source = paper.get('source', 'Unknown')
                url = paper.get('url', '#')
                published = paper.get('published', 'n.d.')
                
                report += f"{i}. {authors}. ({published}). *{title}*. {source}. [{url}]({url})\n\n"
            
            return report
    
    except Exception as e:
        return {"error": f"Error generating research report: {str(e)}"} 