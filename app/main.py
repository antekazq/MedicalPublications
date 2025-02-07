from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import os
from dotenv import load_dotenv
from database.database import insert_publication, insert_journal
from datetime import datetime

#Load environment variables from .env
load_dotenv()

#Use
app = FastAPI()
templates = Jinja2Templates(directory="templates")

#Home route to display the searchbar
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "results": ""})

#Handle form submissions and search for PubMed articles
@app.post("/", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...)):
    articles = search_pubmed(query)
    
    #Format results as an HTML table
    if articles:
        results = f"<h3>Result: {query}</h3>"
        results += "<table border='1'><tr><th>Title</th><th>Journal</th><th>Year</th><th>DOI</th></tr>"
        for article in articles:
            results += f"<tr><td>{article['Title']}</td><td>{article['Journal']}</td><td>{article['Year']}</td><td>{article['DOI']}</td></tr>"
        results += "</table>"
    else:
        results = "<p>No articles were found.</p>"

    return templates.TemplateResponse("index.html", {"request": request, "results": results})


#To shorten abstracts to a word limit
def shorten_abstract(abstract, word_limit=30):
    words = abstract.split()
    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + "..."
    return abstract

 #Set default to January 1st of the given year
def format_year_to_date(year):
    if year:
        return f"{year}-01-01"  
    return None

#Search articles
def search_pubmed(query, max_results=5):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'api_key': os.getenv("API_KEY")
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []

    from xml.etree import ElementTree as ET
    root = ET.fromstring(response.content)
    pubmed_ids = [id_elem.text for id_elem in root.findall(".//Id")]
    
    return fetch_pubmed_details(pubmed_ids)

#Fetch detailed information for a list of PubMed IDs
def fetch_pubmed_details(pubmed_ids):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    params = {
        'db': 'pubmed',
        'id': ','.join(pubmed_ids),
        'retmode': 'xml',
        'api_key': os.getenv("API_KEY")
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []

    from xml.etree import ElementTree as ET
    root = ET.fromstring(response.content)
    articles = []

    #Process each article's data
    for article in root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle", "Unknown")
        journal = article.findtext(".//Journal/Title", "Unknown")
        abstract = article.findtext(".//AbstractText", "Unknown")
        short_abstract = shorten_abstract(abstract)

        pub_date = article.findtext(".//PubDate/Year", "Unknown")
        formatted_date = format_year_to_date(pub_date)

        #Extract DOI code if available
        doi = None
        for id_elem in article.findall(".//ArticleId"):
            if id_elem.attrib.get('IdType') == 'doi':
                doi = id_elem.text
                break

        #Insert journal and publication into the database
        journal_id = insert_journal(journal)
        insert_publication(formatted_date, title, short_abstract, journal_id, doi)

        articles.append({
            "Title": title,
            "Journal": journal,
            "Year": pub_date,
            "DOI": doi or "Unknown"
        })

    return articles
