from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from sqlmodel import Session, select
from datetime import datetime

from models import Document, DocumentAnalysis, engine, create_db_and_tables
from text_analyzer import analyzer

# Initialize FastAPI app
app = FastAPI(
    title="Document Analyzer API",
    description="A text analysis API that analyzes documents for sentiment, keywords, and readability",
    version="1.0.0"
)

# Pydantic models for API requests/responses
class DocumentCreate(BaseModel):
    title: str
    content: str
    author: Optional[str] = None
    category: Optional[str] = None

class SentimentRequest(BaseModel):
    text: str

class KeywordRequest(BaseModel):
    text: str
    limit: Optional[int] = 10

class SearchRequest(BaseModel):
    query: str

class DocumentResponse(BaseModel):
    id: int
    title: str
    author: Optional[str]
    category: Optional[str]
    created_at: datetime
    content_preview: str

class DocumentAnalysisResponse(BaseModel):
    document_id: int
    title: str
    author: Optional[str]
    category: Optional[str]
    analysis: Dict[str, Any]

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

@app.get("/")
async def root():
    return {
        "message": "Document Analyzer API",
        "endpoints": {
            "analyze_document": "/analyze/{document_id}",
            "get_sentiment": "/sentiment",
            "extract_keywords": "/keywords", 
            "add_document": "/documents",
            "search_documents": "/search",
            "list_documents": "/documents"
        }
    }

@app.post("/documents", response_model=Dict[str, Any])
async def add_document(document: DocumentCreate):
    """Add a new document to the database"""
    with Session(engine) as session:
        db_document = Document(
            title=document.title,
            content=document.content,
            author=document.author,
            category=document.category
        )
        
        session.add(db_document)
        session.commit()
        session.refresh(db_document)
        
        return {
            "message": "Document added successfully",
            "document_id": db_document.id,
            "title": db_document.title
        }

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents():
    """List all documents"""
    with Session(engine) as session:
        documents = session.exec(select(Document)).all()
        
        results = []
        for doc in documents:
            results.append(DocumentResponse(
                id=doc.id,
                title=doc.title,
                author=doc.author,
                category=doc.category,
                created_at=doc.created_at,
                content_preview=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            ))
        
        return results

@app.get("/analyze/{document_id}", response_model=DocumentAnalysisResponse)
async def analyze_document(document_id: int):
    """Perform complete analysis of a document by ID"""
    with Session(engine) as session:
        # Get document
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        # Perform analysis
        analysis_results = analyzer.analyze_full_document(document.content)
        
        # Save analysis to database
        db_analysis = DocumentAnalysis(
            document_id=document_id,
            sentiment_polarity=analysis_results["sentiment"]["polarity"],
            sentiment_subjectivity=analysis_results["sentiment"]["subjectivity"],
            sentiment_label=analysis_results["sentiment"]["label"],
            keywords=json.dumps(analysis_results["keywords"]),
            flesch_reading_ease=analysis_results["readability"]["flesch_reading_ease"],
            flesch_kincaid_grade=analysis_results["readability"]["flesch_kincaid_grade"],
            gunning_fog=analysis_results["readability"]["gunning_fog"],
            word_count=analysis_results["stats"]["word_count"],
            sentence_count=analysis_results["stats"]["sentence_count"],
            char_count=analysis_results["stats"]["char_count"]
        )
        
        session.add(db_analysis)
        session.commit()
        
        # Format response
        return DocumentAnalysisResponse(
            document_id=document_id,
            title=document.title,
            author=document.author,
            category=document.category,
            analysis={
                "sentiment": {
                    "polarity": analysis_results["sentiment"]["polarity"],
                    "subjectivity": analysis_results["sentiment"]["subjectivity"],
                    "label": analysis_results["sentiment"]["label"]
                },
                "keywords": analysis_results["keywords"],
                "readability": {
                    "flesch_reading_ease": analysis_results["readability"]["flesch_reading_ease"],
                    "flesch_kincaid_grade": analysis_results["readability"]["flesch_kincaid_grade"],
                    "gunning_fog": analysis_results["readability"]["gunning_fog"]
                },
                "stats": {
                    "word_count": analysis_results["stats"]["word_count"],
                    "sentence_count": analysis_results["stats"]["sentence_count"],
                    "char_count": analysis_results["stats"]["char_count"]
                }
            }
        )

@app.post("/sentiment", response_model=Dict[str, Any])
async def get_sentiment(request: SentimentRequest):
    """Get sentiment analysis for text"""
    sentiment = analyzer.analyze_sentiment(request.text)
    return sentiment

@app.post("/keywords", response_model=Dict[str, List[str]])
async def extract_keywords(request: KeywordRequest):
    """Extract keywords from text"""
    keywords = analyzer.extract_keywords(request.text, request.limit)
    return {"keywords": keywords}

@app.post("/search", response_model=Dict[str, Any])
async def search_documents(request: SearchRequest):
    """Search documents by content"""
    with Session(engine) as session:
        # Simple text search in title and content
        statement = select(Document).where(
            (Document.title.contains(request.query)) | 
            (Document.content.contains(request.query))
        )
        documents = session.exec(statement).all()
        
        results = []
        for doc in documents:
            results.append({
                "id": doc.id,
                "title": doc.title,
                "author": doc.author,
                "category": doc.category,
                "created_at": doc.created_at.isoformat(),
                "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            })
        
        return {
            "query": request.query,
            "results_count": len(results),
            "documents": results
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 