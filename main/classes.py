from pydantic import BaseModel, model_validator
from typing import List, Optional
import json

class Company(BaseModel):
    name: str

class Sector(BaseModel):
    name: str

class Article(BaseModel):
    companies: List[Company]       # List of Company objects
    sectors: List[Sector]          # List of Sector objects
    summary: str
    relevance: int                 # 1-10 scale
    businesses: Optional[List[str]] = None
    extra_info: Optional[List[str]] = None
    url: Optional[str] = None

    @model_validator(mode='before')
    def convert_nested(cls, values):
        # Convert company strings to Company objects
        companies = values.get("companies", [])
        values["companies"] = [c if isinstance(c, Company) else Company(name=c) for c in companies]

        # Convert sector strings to Sector objects
        sectors = values.get("sectors", [])
        values["sectors"] = [s if isinstance(s, Sector) else Sector(name=s) for s in sectors]

        return values


# These classes below follow the structure of a Gemini response, allowing seamless parsing

class ContentPart(BaseModel):
    text: str
    parsed_articles: List[Article] = []

    @model_validator(mode='before')
    def parse_articles(cls, values):

        text = values.get('text')
       
        cleaned = text.replace("```json", "").replace("```", "").strip()
        try:
            parsed_list = json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")

        
        values['parsed_articles'] = [Article(**item) for item in parsed_list]
        return values



class Content(BaseModel):
    parts: List[ContentPart]
    role: str

class Candidate(BaseModel):
    content: Content
    finishReason: str
    index: int


class TokenDetail(BaseModel):
    modality: str
    tokenCount: int

class UsageMetadata(BaseModel):
    promptTokenCount: int
    candidatesTokenCount: int
    totalTokenCount: int
    promptTokensDetails: List[TokenDetail]
    thoughtsTokenCount: int


class GeminiAPIResponse(BaseModel):
    candidates: List[Candidate]
    usageMetadata: UsageMetadata
    modelVersion: str
    responseId: str

