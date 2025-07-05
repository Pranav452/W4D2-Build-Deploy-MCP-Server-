from sqlmodel import SQLModel, Field, Relationship, create_engine, Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    author: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    analyses: List["DocumentAnalysis"] = Relationship(back_populates="document")


class DocumentAnalysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    
    # Sentiment analysis results
    sentiment_polarity: float  # -1 to 1 (negative to positive)
    sentiment_subjectivity: float  # 0 to 1 (objective to subjective)
    sentiment_label: str  # "positive", "negative", "neutral"
    
    # Keywords (stored as JSON string)
    keywords: str  # JSON list of keywords
    
    # Readability scores
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float
    
    # Basic stats
    word_count: int
    sentence_count: int
    char_count: int
    
    # Analysis metadata
    analyzed_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    document: Optional[Document] = Relationship(back_populates="analyses")
    
    def get_keywords_list(self) -> List[str]:
        """Convert keywords JSON string to list"""
        return json.loads(self.keywords) if self.keywords else []
    
    def set_keywords_list(self, keywords_list: List[str]) -> None:
        """Convert keywords list to JSON string"""
        self.keywords = json.dumps(keywords_list)


# Database setup
DATABASE_URL = "sqlite:///./document_analyzer.db"
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session 