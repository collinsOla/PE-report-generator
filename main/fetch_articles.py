from main.classes import GeminiAPIResponse
import os
from dotenv import load_dotenv
import requests
import json
from database.queries import insert_article

load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def loadNews(search):
    params = {
        "q": search, #Searches for news articles that mention this search argument
        "pageSize": 5, #Fetches 5 articles
        "apiKey": NEWSAPI_KEY
    }
    data = requests.get(f'https://newsapi.org/v2/everything', params=params)
    return data.json()['articles']


def getArticleData(urls):
    headers = {
        'x-goog-api-key': GEMINI_API_KEY,
        'Content-Type': 'application/json' #Gemini Output in Json
    }
    data = {
            "contents": [{"parts": [{"text": "Give me a list of all companies ('companies') involved in the source, sectors ('sectors') involved each of the sources, a single summary ('summary' ) of each source, and a relevance index for each source ('relevance') on how useful it is regarding potential private equity deal opportuninities from UK business news ranging from 1-10, Concise summaries of the relevant businesses mentioned ('businesses' as a list of strings), any extra useful information ('extra_info' as a list of strings), and the URL ('url')" ,},
            {"text": "Ensure this is in an immediately JSON serialisable format with only the data I require as keys"}, 
            {"text": f'The provided data is {urls}'}]}]
    }
    geminiResponse = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent", headers=headers, json=data)
    if geminiResponse.status_code != 200:
        return None #Ignore data when status code is invalid (if occurs, likely to be due to Gemini which isn't as predictable)
    
    return json.loads(geminiResponse.text)
           

def processArticle(geminiResponse):
    if geminiResponse == None:
        return None #Use of this function as an applicative
    gemini_obj = GeminiAPIResponse.model_validate(geminiResponse)
    proccessedArticles = gemini_obj.candidates[0].content.parts[0].parsed_articles
    for article in proccessedArticles:
        insert_article(article) #Insert all these processed articles into the database
 
    
def main():
    # List of search keywords potentially relating to private equity
    for topic in ["finance", "business", "economics", "investing", "private equity", "venture capital", "buyout", "fundraising", "mergers", "acquisitions", "portfolio companies", "investment opportunities", "capital markets", "growth equity", "financial transactions", "deal flow", "corporate finance", "investment strategy", "fund management", "capital raising"]:
        processArticle(getArticleData(json.dumps(loadNews(topic))))
    