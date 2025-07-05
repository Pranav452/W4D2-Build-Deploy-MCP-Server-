# Document Analyzer API

A powerful document analysis API that analyzes text documents for sentiment, keywords, and readability. Built with FastAPI, SQLModel, TextBlob, and Textstat following the MCP (Model Context Protocol) design principles.

## Features

- **Sentiment Analysis**: Analyze text for polarity (-1 to 1) and subjectivity (0 to 1)
- **Keyword Extraction**: Extract top keywords and phrases from documents
- **Readability Scoring**: Calculate Flesch Reading Ease, Flesch-Kincaid Grade, and Gunning Fog scores
- **Document Storage**: Store and manage documents with metadata in SQLite database
- **Search Functionality**: Search documents by content and metadata
- **Basic Statistics**: Word count, sentence count, and character count
- **REST API**: Full REST API with automatic OpenAPI documentation

## Tech Stack

- **API Framework**: FastAPI
- **Server**: Uvicorn
- **Database**: SQLite with SQLModel ORM
- **Text Analysis**: TextBlob and Textstat
- **Environment**: Python 3.9+

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd document-analyzer
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download TextBlob corpora** (if not automatically downloaded):
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"
   ```

## Setup

1. **Initialize the database with sample data**:
   ```bash
   python populate_sample_data.py
   ```
   This creates the SQLite database and adds 18 sample documents covering various topics.

2. **Start the API server**:
   ```bash
   python document_analyzer_api.py
   ```
   
   The API will be available at:
   - **API**: http://localhost:8000
   - **Interactive Docs**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Document Management

#### `POST /documents`
Add a new document to the database.

**Request Body**:
```json
{
  "title": "Document Title",
  "content": "Document content...",
  "author": "Author Name (optional)",
  "category": "Category (optional)"
}
```

#### `GET /documents`
List all documents with previews.

#### `GET /analyze/{document_id}`
Perform complete analysis of a document by ID.

**Returns**: Complete analysis including sentiment, keywords, readability scores, and basic statistics.

### Text Analysis

#### `POST /sentiment`
Analyze sentiment of any text.

**Request Body**:
```json
{
  "text": "Text to analyze for sentiment"
}
```

**Returns**: Polarity, subjectivity, and sentiment label (positive/negative/neutral).

#### `POST /keywords`
Extract top keywords from text.

**Request Body**:
```json
{
  "text": "Text to extract keywords from",
  "limit": 10
}
```

**Returns**: List of top keywords.

#### `POST /search`
Search documents by content or metadata.

**Request Body**:
```json
{
  "query": "search terms"
}
```

**Returns**: List of matching documents with previews.

## Usage Examples

### Using curl

```bash
# Add a new document
curl -X POST "http://localhost:8000/documents" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "My Test Document",
       "content": "This is a wonderful example of text analysis. The system works great!",
       "author": "John Doe",
       "category": "Test"
     }'

# Analyze the document (assuming it got ID 1)
curl -X GET "http://localhost:8000/analyze/1"

# Get sentiment for custom text
curl -X POST "http://localhost:8000/sentiment" \
     -H "Content-Type: application/json" \
     -d '{"text": "This is a wonderful day!"}'

# Extract keywords
curl -X POST "http://localhost:8000/keywords" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Machine learning and artificial intelligence are transforming technology.",
       "limit": 5
     }'

# Search documents
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "artificial intelligence"}'
```

### Using Python requests

```python
import requests

# Add a document
response = requests.post("http://localhost:8000/documents", json={
    "title": "AI Research Paper",
    "content": "Artificial intelligence has revolutionized many fields...",
    "author": "Dr. Smith",
    "category": "Research"
})
print(response.json())

# Analyze the document
doc_id = response.json()["document_id"]
analysis = requests.get(f"http://localhost:8000/analyze/{doc_id}")
print(analysis.json())

# Get sentiment
sentiment = requests.post("http://localhost:8000/sentiment", json={
    "text": "This is an amazing breakthrough in technology!"
})
print(sentiment.json())
```

## Sample Data

The system comes with 18 sample documents covering various topics:

1. **Technology**: AI, Quantum Computing, Transportation
2. **Environment**: Climate Change, Biodiversity, Energy
3. **Health & Wellness**: Sleep Science, Mindfulness, Cooking
4. **Social Sciences**: Psychology, Philosophy, Sociology
5. **Arts & Culture**: Music, Literature, Storytelling
6. **Science**: Space Exploration, Conservation, Mathematics

## Database Schema

### Documents Table
- `id`: Primary key
- `title`: Document title
- `content`: Document content
- `author`: Document author (optional)
- `category`: Document category (optional)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### DocumentAnalysis Table
- `id`: Primary key
- `document_id`: Foreign key to documents
- `sentiment_polarity`: Sentiment polarity (-1 to 1)
- `sentiment_subjectivity`: Sentiment subjectivity (0 to 1)
- `sentiment_label`: Sentiment label (positive/negative/neutral)
- `keywords`: JSON array of keywords
- `flesch_reading_ease`: Flesch Reading Ease score
- `flesch_kincaid_grade`: Flesch-Kincaid Grade Level
- `gunning_fog`: Gunning Fog Index
- `word_count`: Number of words
- `sentence_count`: Number of sentences
- `char_count`: Number of characters
- `analyzed_at`: Analysis timestamp

## Analysis Details

### Sentiment Analysis
- Uses TextBlob's polarity and subjectivity scores
- Polarity ranges from -1 (negative) to 1 (positive)
- Subjectivity ranges from 0 (objective) to 1 (subjective)
- Labels: positive (>0.1), negative (<-0.1), neutral (between -0.1 and 0.1)

### Keyword Extraction
- Filters out common stop words
- Includes both individual words and noun phrases
- Frequency-based ranking
- Configurable limit for number of keywords returned

### Readability Scores
- **Flesch Reading Ease**: Higher scores indicate easier reading
- **Flesch-Kincaid Grade**: U.S. grade level required to understand the text
- **Gunning Fog Index**: Years of formal education needed to understand the text

## File Structure

```
document-analyzer/
├── document_analyzer_api.py  # Main FastAPI application
├── models.py                 # SQLModel database models
├── text_analyzer.py         # Text analysis utilities
├── populate_sample_data.py  # Script to add sample documents
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── document_analyzer.db    # SQLite database (created after setup)
```

## API Documentation

Once the server is running, you can access:

- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **OpenAPI JSON Schema**: http://localhost:8000/openapi.json

## Development

### Running Tests
```bash
# Add your test files and run with pytest
pytest tests/
```

### Adding New Analysis Features
1. Add new analysis methods to `TextAnalyzer` class in `text_analyzer.py`
2. Update database model in `models.py` if needed
3. Add new API endpoints in `document_analyzer_api.py`
4. Update documentation

### Customizing Analysis
- Modify stop words list in `text_analyzer.py`
- Adjust sentiment thresholds for labeling
- Add new readability metrics using textstat
- Implement custom keyword extraction algorithms

## MCP Compatibility

This API is designed following MCP (Model Context Protocol) principles and can easily be adapted to work as a formal MCP server when using Python 3.10+ environments. The current implementation provides the same functionality through a standard REST API that's compatible with any HTTP client.

To convert to a formal MCP server:
1. Upgrade to Python 3.10+
2. Install the official MCP Python SDK
3. Replace the FastAPI routes with MCP tool definitions
4. Use the `mcp_server.py` template (included but requires Python 3.10+)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Text analysis powered by [TextBlob](https://textblob.readthedocs.io/)
- Readability scoring using [Textstat](https://github.com/textstat/textstat)
- Database management with [SQLModel](https://sqlmodel.tiangolo.com/)
- Inspired by the [Model Context Protocol](https://modelcontextprotocol.io/) 