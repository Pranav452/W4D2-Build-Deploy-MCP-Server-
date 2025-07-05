import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from sqlmodel import Session, select
from datetime import datetime

from models import Document, DocumentAnalysis, engine, create_db_and_tables
from text_analyzer import analyzer


class DocumentAnalyzerServer:
    """MCP Server for Document Analysis"""
    
    def __init__(self):
        self.server = Server("document-analyzer")
        self.setup_tools()
        
    def setup_tools(self):
        """Setup all MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools"""
            return [
                Tool(
                    name="analyze_document",
                    description="Perform complete analysis of a document by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_id": {
                                "type": "integer",
                                "description": "ID of the document to analyze"
                            }
                        },
                        "required": ["document_id"]
                    }
                ),
                Tool(
                    name="get_sentiment",
                    description="Analyze sentiment of any text",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to analyze for sentiment"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="extract_keywords",
                    description="Extract top keywords from text",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to extract keywords from"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of keywords to return",
                                "default": 10
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="add_document",
                    description="Add a new document to the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the document"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content of the document"
                            },
                            "author": {
                                "type": "string",
                                "description": "Author of the document",
                                "default": None
                            },
                            "category": {
                                "type": "string",
                                "description": "Category of the document",
                                "default": None
                            }
                        },
                        "required": ["title", "content"]
                    }
                ),
                Tool(
                    name="search_documents",
                    description="Search documents by content or metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find documents"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            if name == "analyze_document":
                return await self._analyze_document(arguments["document_id"])
            elif name == "get_sentiment":
                return await self._get_sentiment(arguments["text"])
            elif name == "extract_keywords":
                limit = arguments.get("limit", 10)
                return await self._extract_keywords(arguments["text"], limit)
            elif name == "add_document":
                return await self._add_document(arguments)
            elif name == "search_documents":
                return await self._search_documents(arguments["query"])
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _analyze_document(self, document_id: int) -> List[TextContent]:
        """Analyze a document by ID"""
        with Session(engine) as session:
            # Get document
            document = session.get(Document, document_id)
            if not document:
                return [TextContent(
                    type="text",
                    text=f"Document with ID {document_id} not found"
                )]
            
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
            result = {
                "document_id": document_id,
                "title": document.title,
                "author": document.author,
                "category": document.category,
                "analysis": {
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
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
    
    async def _get_sentiment(self, text: str) -> List[TextContent]:
        """Get sentiment analysis for text"""
        sentiment = analyzer.analyze_sentiment(text)
        
        return [TextContent(
            type="text",
            text=json.dumps(sentiment, indent=2)
        )]
    
    async def _extract_keywords(self, text: str, limit: int) -> List[TextContent]:
        """Extract keywords from text"""
        keywords = analyzer.extract_keywords(text, limit)
        
        return [TextContent(
            type="text",
            text=json.dumps({"keywords": keywords}, indent=2)
        )]
    
    async def _add_document(self, document_data: Dict[str, Any]) -> List[TextContent]:
        """Add a new document"""
        with Session(engine) as session:
            document = Document(
                title=document_data["title"],
                content=document_data["content"],
                author=document_data.get("author"),
                category=document_data.get("category")
            )
            
            session.add(document)
            session.commit()
            session.refresh(document)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "message": "Document added successfully",
                    "document_id": document.id,
                    "title": document.title
                }, indent=2)
            )]
    
    async def _search_documents(self, query: str) -> List[TextContent]:
        """Search documents by content"""
        with Session(engine) as session:
            # Simple text search in title and content
            statement = select(Document).where(
                (Document.title.contains(query)) | 
                (Document.content.contains(query))
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
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "results_count": len(results),
                    "documents": results
                }, indent=2)
            )]
    
    async def run(self):
        """Run the MCP server"""
        # Initialize database
        create_db_and_tables()
        
        # Run server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, 
                write_stream,
                InitializationOptions(
                    server_name="document-analyzer",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main function to run the server"""
    server = DocumentAnalyzerServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 