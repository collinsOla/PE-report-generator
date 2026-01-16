import os
from dotenv import load_dotenv
import requests
import json

#Database work
from sqlalchemy import create_engine

#Analysis
import pandas as pd
import numpy as np
import networkx as nx

#report
import markdown2
from fpdf import FPDF
import re

engine = create_engine("sqlite:///database/articles.db", echo=False)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


#Data frames
articles_df = pd.read_sql("SELECT * FROM article", engine)
companies_df = pd.read_sql("SELECT * FROM company", engine)
sectors_df = pd.read_sql("SELECT * FROM sector", engine)
article_company_df = pd.read_sql("SELECT * FROM article_company", engine)
article_sector_df = pd.read_sql("SELECT * FROM article_sector", engine)

def analyseSectors():

    merged = article_sector_df.merge(
        articles_df,
        left_on="article_id",
        right_on="id"
    ).merge(
        sectors_df,
        left_on="sector_id",
        right_on="id",
        suffixes=("_article", "_sector") #Make data frame merging sectors and their articles
    )

    sector_stats = merged.groupby("name").agg(
    avg_relevance=("relevance", "mean"),
    article_count=("article_id", "count")
    ).reset_index() #Calculating mean of relevence of each sector, and frequency of articles

    sector_stats["weighted_score"] = sector_stats["avg_relevance"] * np.log(sector_stats["article_count"]+1) # Calculating a weighted score 
    sector_stats = sector_stats.sort_values(by="weighted_score", ascending=False)

    return sector_stats

def analyseCompanies():

    merged = article_company_df.merge(
        articles_df,
        left_on="article_id",
        right_on="id"
    ).merge(
        companies_df,
        left_on="company_id",
        right_on="id",
        suffixes=("_article", "_company") # merging companies and their articles
    )

    company_stats = merged.groupby("name").agg(
    avg_relevance=("relevance", "mean"),
    article_count=("article_id", "count")
    ).reset_index() #Calculating mean of relevence of each company, and frequency of articles

    company_stats["weighted_score"] = company_stats["avg_relevance"] * np.log(company_stats["article_count"]+1) # Calculating a weighted score 
    company_stats = company_stats.sort_values(by="weighted_score", ascending=False)

    return company_stats
   

def computeEigenCentrality():
    graph = nx.Graph() #Create a graph

    merged = (
    article_sector_df
    .merge(articles_df, left_on="article_id", right_on="id")
    .merge(sectors_df, left_on="sector_id", right_on="id", suffixes=("_article", "_sector"))
    .merge(article_company_df, on="article_id")
    .merge(companies_df, left_on="company_id", right_on="id", suffixes=("_company", "_sector")))
    #Merge all dataframes together into a flat frame


    for _, row in merged.iterrows():
        company = row["name_company"]
        sector = row["name_sector"]
        relevance = row["relevance"]
        graph.add_edge(company, sector, weight=relevance) #Iteratively create weighted graph (nodes=company/sector, edges = relevence of article)

    eigen_centrality = nx.eigenvector_centrality(graph, weight="weight", max_iter=1000, tol=1e-04)
    centrality_df = pd.DataFrame(list(eigen_centrality.items()), columns=["node", "eigen_centrality"])

    centrality_df["eigen_centrality_norm"] = (
    (centrality_df["eigen_centrality"] - centrality_df["eigen_centrality"].min()) /
    (centrality_df["eigen_centrality"].max() - centrality_df["eigen_centrality"].min())
    ) # Calculate normalised eigen centrality
    return centrality_df.sort_values(by="eigen_centrality", ascending=False)


def filterSectors():
    sector_df = analyseSectors()
    centrality_df = computeEigenCentrality()
    sector_centrality_df = centrality_df[centrality_df["node"].isin(sector_df["name"])].copy()
    sector_centrality_df = sector_centrality_df.rename(columns={"node": "name"})
    sector_df = sector_df.merge(sector_centrality_df, on="name")

    percentile_cutoff = 0.5

    # Compute thresholds for each metric
    relevance_thresh = sector_df["avg_relevance"].quantile(percentile_cutoff)
    article_count_thresh = sector_df["article_count"].quantile(percentile_cutoff)
    centrality_thresh = sector_df["eigen_centrality"].quantile(percentile_cutoff)
    # Only return sectors in the upper quartiles of relevence, article count, and centrality
    return sector_df[(sector_df["avg_relevance"] >= relevance_thresh) & (sector_df["article_count"] >= article_count_thresh) & (sector_df["eigen_centrality"] >= centrality_thresh)].drop(columns="eigen_centrality")

def filterCompanies():
    company_df = analyseCompanies()
    centrality_df = computeEigenCentrality()
    company_centrality_df = centrality_df[centrality_df["node"].isin(company_df["name"])].copy()
    company_centrality_df = company_centrality_df.rename(columns={"node": "name"})
    company_df = company_df.merge(company_centrality_df, on="name")

    percentile_cutoff = 0.5

    relevance_thresh = company_df["avg_relevance"].quantile(percentile_cutoff)
    article_count_thresh = company_df["article_count"].quantile(percentile_cutoff)
    centrality_thresh = company_df["eigen_centrality"].quantile(percentile_cutoff)
    # Only return companies in the upper quartiles of relevence, article count, and centrality
    return company_df[(company_df["avg_relevance"] >= relevance_thresh) & (company_df["article_count"] >= article_count_thresh) & (company_df["eigen_centrality"] >= centrality_thresh)]


def filterArticles():
    percentile_cutoff = 0.5
    relevance_thresh = articles_df["relevance"].quantile(percentile_cutoff)
    #Only return articles in the upper quartiles of relevence
    return articles_df[(articles_df["relevance"] > relevance_thresh)]


def generateReport():
    headers = {
        'x-goog-api-key': GEMINI_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
            "contents": [{"parts": [{"text": "Based on this data, generate a detailed report on potential private equity deal opportunities in the UK, using high level analysis"},
            {"text": "Base your analysis only on the provided dataset and metrics."},
            {"text": "Focus on trends, relative importance, and actionable insights."},
            {"text": f'Relevant_Articles : {filterArticles().to_json(orient="records", lines=False)}'},
            {"text": f'Relevant_Sectors : {filterSectors().to_json(orient="records", lines=False)}'},
            {"text": f'Relevant_Companies : {filterCompanies().to_json(orient="records", lines=False)}'},
            {"text": "Relevance: How important or newsworthy this article is (higher = more significant)."},
            {"text": "Centrality: signals strategic influence or interdependence — a sector with high centrality is “well-positioned” in the ecosystem."},     
            {"text": "Include no other exposition, just the report"},
            {"text": "If specific articles are ever reffered to, use the link as the identifier not the ID"}]}]
    }

    #Gemini prompt to generate repoty
    geminiResponse = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent", headers=headers, json=data)
    return json.loads(geminiResponse.text)["candidates"][0]["content"]["parts"][0]["text"]


def writeReport(filePath):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Uses regex to convert markdown into pdf text
    for line in generateReport().split("\n"):
        #Headings
        if line.startswith("### "):
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 8, line[4:])
            pdf.set_font("Arial", size=12)
        elif line.startswith("## "):
            pdf.set_font("Arial", "B", 14)
            pdf.multi_cell(0, 8, line[3:])
            pdf.set_font("Arial", size=12)
        elif line.startswith("# "):
            pdf.set_font("Arial", "B", 16)
            pdf.multi_cell(0, 8, line[2:])
            pdf.set_font("Arial", size=12)
        #Bullets
        elif line.startswith("* "):
            pdf.multi_cell(0, 8, "- " + line[2:])
        #Bold
        else:
            line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)  
            pdf.multi_cell(0, 8, line)

    pdf.output(filePath) #Create pdf


