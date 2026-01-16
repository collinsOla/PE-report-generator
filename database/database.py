from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Table, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

engine = create_engine("sqlite:///database/articles.db", echo=False)
SessionLocal = sessionmaker(bind=engine)


article_company = Table(
    "article_company",
    Base.metadata,
    Column("article_id", ForeignKey("article.id"), primary_key=True),
    Column("company_id", ForeignKey("company.id"), primary_key=True),
)

article_sector = Table(
    "article_sector",
    Base.metadata,
    Column("article_id", ForeignKey("article.id"), primary_key=True),
    Column("sector_id", ForeignKey("sector.id"), primary_key=True),
)

class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class Sector(Base):
    __tablename__ = "sector"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True)
    summary = Column(Text, nullable=False)
    relevance = Column(Integer, nullable=False)
    url = Column(String)

    companies = relationship(
        "Company",
        secondary=article_company,
        backref="articles"
    )

    sectors = relationship(
        "Sector",
        secondary=article_sector,
        backref="articles"
    )

Base.metadata.create_all(engine)


