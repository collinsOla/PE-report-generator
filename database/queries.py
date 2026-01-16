from main.classes import GeminiAPIResponse, Article, Company, Sector
from sqlalchemy.orm import Session
import database.database as DB


db = DB.SessionLocal()

#Create database model
def get_or_create(model, name):
    instance = db.query(model).filter_by(name=name).first()
    if not instance:
        instance = model(name=name)
        db.add(instance)
        db.commit()
        db.refresh(instance)
    return instance

#Insert object article into database
def insert_article(article):
    db_article = DB.Article(    
        summary=article.summary,
        relevance=article.relevance,
        url=article.url,
    )


    db_article.companies = [
        get_or_create(DB.Company, c.name)
        for c in article.companies
    ]


    db_article.sectors = [
        get_or_create(DB.Sector, s.name)
        for s in article.sectors
    ]

    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article

#Convert a database article into a pydantic class article
def db_article_to_pydantic(db_article):
    return Article(
        summary=db_article.summary,
        relevance=db_article.relevance,
        url=db_article.url,
        companies=[Company(name=c.name) for c in db_article.companies],
        sectors=[Sector(name=s.name) for s in db_article.sectors],
    )

#Generate all articles from the database
def load_all_articles():
    articles = db.query(DB.Article).all()  
    return [db_article_to_pydantic(a) for a in articles]