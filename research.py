import asyncio
import requests
import chainlit as cl
from agents import Agent, Runner
from typing import List, Optional
from pydantic import BaseModel, Field
from xml.etree import ElementTree as ET
import time
import urllib3
import os

# from IPython.display import Markdown, display
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# gemini_api_key = os.getenv("GEMINI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY") 

# Disable warnings for retries (optional)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Pydantic models
class Paper(BaseModel):
    title: str
    abstract: str
    url: str

class ConsensusMeter(BaseModel):
    yes: Optional[str] = None
    possibly: Optional[str] = None
    no: Optional[str] = None

class Insights(BaseModel):
    title: str
    insight: str
    url: str

class LLMResponseStructure(BaseModel):
    insights: List[Insights]
    consensus_meter: Optional[ConsensusMeter] = None
    short_summary: str
    conclusion: str

# Search functions
def semantic_scholar_search(query: str, limit: int) -> List[dict]:
    try:
        base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": query, "limit": limit, "fields": "title,abstract,url"}
        retries, delay = 3, 5

        for attempt in range(retries):
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                papers = [
                    {
                        "title": paper.get("title", "No title available"),
                        "abstract": paper.get("abstract", "No abstract available"),
                        "url": paper.get("url", "No URL available")
                    }
                    for paper in data.get("data", [])
                ]
                return papers
            elif response.status_code == 429:
                print(f"Rate limited by Semantic Scholar API. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                response.raise_for_status()
        print("Exceeded maximum retry attempts for Semantic Scholar.")
        return []
    except Exception as e:
        print(f"Error during Semantic Scholar search: {e}")
        return []

def pubmed_search(query: str, limit: int) -> List[dict]:
    try:
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        retries, delay = 5, 5

        # Optional: Add NCBI API key if available
        # ncbi_api_key = "your-ncbi-api-key"  # Uncomment and set if you have one
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": limit,
            # "api_key": ncbi_api_key
        }

        for attempt in range(retries):
            try:
                search_response = requests.get(base_url, params=search_params, timeout=20, verify=False)
                search_response.raise_for_status()
                pmids = search_response.json().get("esearchresult", {}).get("idlist", [])
                break
            except (requests.exceptions.ConnectTimeout, requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
                print(f"PubMed search attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
        else:
            print("Exceeded maximum retries for PubMed search.")
            return []

        if not pmids:
            print("No PubMed articles found.")
            return []

        for attempt in range(retries):
            try:
                fetch_params = {
                    "db": "pubmed",
                    "id": ",".join(pmids),
                    "retmode": "xml",
                    # "api_key": ncbi_api_key
                }
                fetch_response = requests.get(fetch_url, params=fetch_params, timeout=20, verify=False)
                fetch_response.raise_for_status()
                root = ET.fromstring(fetch_response.text)
                papers = []

                for article in root.findall(".//PubmedArticle"):
                    title = article.findtext(".//ArticleTitle", default="No title available")
                    abstract = article.findtext(".//AbstractText", default="No abstract available")
                    pmid = article.findtext(".//PMID", default="No ID available")
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "No URL available"
                    papers.append({"title": title, "abstract": abstract, "url": url})

                return papers
            except (requests.exceptions.ConnectTimeout, requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
                print(f"PubMed fetch attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
        else:
            print("Exceeded maximum retries for PubMed fetch.")
            return []

    except Exception as e:
        print(f"Error during PubMed search: {e}")
        return []

def arxiv_search(query: str, limit: int) -> List[dict]:
    try:
        from langchain_community.retrievers import ArxivRetriever
        retriever = ArxivRetriever(load_max_docs=limit, get_full_documents=False)
        arxiv_results = retriever.invoke(query)
        papers = [
            {
                "title": doc.metadata.get("Title", "No title available"),
                "abstract": doc.page_content[:500],
                "url": doc.metadata.get("Entry ID", "No URL available")
            }
            for doc in arxiv_results
        ]
        return papers
    except Exception as e:
        print(f"Error during ArXiv search: {e}")
        return []

# Agents
refine_agent = Agent(
    name="RefineAgent",
      # Replace with your API key
    instructions="Refine the provided query to be concise, specific, and clear. Return only the refined query text.",
    model="gpt-4o-mini"
)

semantic_scholar_agent = Agent(
    name="SemanticScholarAgent",
    
    instructions="Fetch relevant research papers from Semantic Scholar based on the provided query and limit.",
    model="gpt-4o-mini"
)

pubmed_agent = Agent(
    name="PubMedAgent",
    
    instructions="Fetch relevant research papers from PubMed based on the provided query and limit.",
    model="gpt-4o-mini"
)

arxiv_agent = Agent(
    name="ArxivAgent",
    
    instructions="Fetch relevant research papers from ArXiv based on the provided query and limit.",
    model="gpt-4o-mini"
)

summarize_agent = Agent(
    name="SummarizeAgent",
    
    instructions=(
        "Analyze research papers and generate a detailed report in the specified JSON format. "
        "For each insight, provide 2-3 sentences explaining the finding in depth, including specific details like methodologies, results, or implications."
    ),
    model="gpt-4o-mini",
    output_type=LLMResponseStructure
)

report_agent = Agent(
    name="ReportAgent",
    
    instructions=(
        "Generate a formatted Markdown report with sections: Query, Short Summary, Consensus Meter, Insights, Conclusion, and Sources. "
        "List each insight with its title, detailed explanation, and clickable URL. "
        "List all unique URLs from insights in the Sources section as bullet points."
    ),
    model="gpt-4o-mini"
)

# Workflow functions
async def refine_query(query: str) -> str:
    prompt = (
        f"You are an expert at refining research queries. "
        f"Refine the following query to be concise and specific.\n"
        f"Original Query: \"{query}\""
    )
    result = await Runner.run(refine_agent, prompt)
    return result.final_output.strip()

async def search_papers(query: str, limit: int) -> tuple[List[dict], List[dict], List[dict]]:
    async def run_search(agent):
        if agent.name == "SemanticScholarAgent":
            return semantic_scholar_search(query, limit)
        elif agent.name == "PubMedAgent":
            return pubmed_search(query, limit)
        elif agent.name == "ArxivAgent":
            return arxiv_search(query, limit)
        return []
    semantic_task = run_search(semantic_scholar_agent)
    pubmed_task = run_search(pubmed_agent)
    arxiv_task = run_search(arxiv_agent)

    semantic_result, pubmed_result, arxiv_result = await asyncio.gather(
        semantic_task, pubmed_task, arxiv_task
    )
    return semantic_result, pubmed_result, arxiv_result

async def summarize_papers(query: str, papers: List[dict]) -> LLMResponseStructure:
    if not papers:
        return LLMResponseStructure(
            short_summary="No papers available for summarization.",
            consensus_meter=None,
            insights=[],
            conclusion="No conclusion available due to lack of papers."
        )
    prompt = (
        f"You are an expert assistant tasked with analyzing research papers on the topic: '{query}'.\n\n"
        "Instructions:\n"
        "1. Query Specificity: If the query is general, set consensus_meter to null. If specific, estimate agreement.\n"
        "2. Summary: Provide a concise overview in short_summary (3-4 sentences).\n"
        "3. Consensus Meter: For specific queries, provide percentages (Yes, Possibly, No).\n"
        "4. Key Insights: Generate 5-7 insights, each with:\n"
        "   - Title: A clear, descriptive title.\n"
        "   - Insight: 2-3 detailed sentences explaining the finding, including methodology, results, or implications.\n"
        "   - URL: The exact URL from the paper.\n"
        "5. Conclusion: Summarize the stance and implications in 2-3 sentences.\n\n"
        "Output Format:\n"
        "```json\n"
        "{\n"
        "  \"insights\": [{\"title\": \"string\", \"insight\": \"string\", \"url\": \"string\"}],\n"
        "  \"consensus_meter\": {\"yes\": \"string\", \"possibly\": \"string\", \"no\": \"string\"} or null,\n"
        "  \"short_summary\": \"string\",\n"
        "  \"conclusion\": \"string\"\n"
        "}\n"
        "```\n\n"
        "Research papers:\n"
    )
    for paper in papers:
        prompt += (
            f"**Title:** {paper['title']}\n"
            f"**Abstract:** {paper['abstract']}\n"
            f"**URL:** {paper['url']}\n\n"
        )
    result = await Runner.run(summarize_agent, prompt)
    return result.final_output

async def generate_report_streaming(query: str, summary_data: LLMResponseStructure, msg: cl.Message):
    insights_str = "\n".join(
        f"- **{insight.title}**: {insight.insight} [Link]({insight.url})"
        for insight in summary_data.insights
    )
    sources_str = "\n".join(
        f"- {insight.url}" for insight in summary_data.insights
    )

    prompt = (
        f"Query: {query}\n"
        f"Short Summary: {summary_data.short_summary}\n"
        # f"Consensus Meter: {summary_data.consensus_meter}\n"
        f"Insights:\n{insights_str}\n"
        f"Conclusion: {summary_data.conclusion}\n"
        f"Sources:\n{sources_str}\n"
        "Generate a formatted Markdown report with sections for Query, Short Summary, Insights, Conclusion, and Sources. "
        "Ensure Insights include the title, detailed explanation, and clickable URL. "
        "List all unique URLs in the Sources section as bullet points."
    )

    result = Runner.run_streamed(report_agent, prompt)

    async for event in result.stream_events():
        if event.type == "raw_response_event" and hasattr(event.data, 'delta'):
            token = event.data.delta
            await msg.stream_token(token)

# Main message handler with loader
@cl.on_message
async def handle_message(message: cl.Message):
    query = message.content.strip()
    if not query:
        await cl.Message(content="Please enter a valid query.").send()
        return
    # Create a message with spinner
    msg = cl.Message(content="Generating report...")
    await msg.send()
    try:
        # Step 1: Refine query
        refined_query = await refine_query(query)
        # Step 2: Search papers
        semantic_papers, pubmed_papers, arxiv_papers = await search_papers(refined_query, limit=5)
        # Step 3: Summarize top N papers
        all_papers = (semantic_papers + pubmed_papers + arxiv_papers)[:5]
        summary_data = await summarize_papers(refined_query, all_papers)

        # Step 4: Generate report with streaming
        await generate_report_streaming(query, summary_data, msg)

    except Exception as e:
        await msg.update()
        await cl.Message(content=f"❌ Error: {str(e)}").send()
