from textblob import TextBlob
import textstat
from typing import List, Dict, Any, Tuple
import re
from collections import Counter


class TextAnalyzer:
    """Text analysis utility class using TextBlob and Textstat"""
    
    def __init__(self):
        # Download required TextBlob corpora (only needs to be done once)
        try:
            import nltk
            nltk.download('punkt', quiet=True)
            nltk.download('brown', quiet=True)
        except:
            pass
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using TextBlob
        Returns polarity (-1 to 1), subjectivity (0 to 1), and label
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine sentiment label
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "label": label
        }
    
    def extract_keywords(self, text: str, limit: int = 10) -> List[str]:
        """
        Extract top keywords from text using TextBlob
        Filters out common stop words and returns most frequent meaningful words
        """
        blob = TextBlob(text)
        
        # Get noun phrases and words
        noun_phrases = blob.noun_phrases
        words = blob.words
        
        # Simple stop words list
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'am', 'is',
            'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'not', 'no',
            'yes', 'very', 'really', 'just', 'now', 'then', 'here', 'there', 'where', 'when', 'how',
            'what', 'who', 'which', 'why', 'all', 'any', 'some', 'each', 'every', 'other', 'another',
            'such', 'only', 'own', 'same', 'so', 'than', 'too', 'more', 'most', 'much', 'many'
        }
        
        # Clean and filter words
        cleaned_words = []
        for word in words:
            word_lower = word.lower()
            if (len(word_lower) > 2 and 
                word_lower not in stop_words and 
                word_lower.isalpha()):
                cleaned_words.append(word_lower)
        
        # Add noun phrases (multi-word concepts)
        for phrase in noun_phrases:
            if len(phrase.split()) > 1:  # Only multi-word phrases
                cleaned_words.append(phrase.lower())
        
        # Count frequency and return top keywords
        word_freq = Counter(cleaned_words)
        top_words = word_freq.most_common(limit)
        
        return [word for word, freq in top_words]
    
    def calculate_readability(self, text: str) -> Dict[str, float]:
        """
        Calculate various readability scores using textstat
        """
        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(text),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
            "gunning_fog": textstat.gunning_fog(text)
        }
    
    def get_basic_stats(self, text: str) -> Dict[str, int]:
        """
        Get basic text statistics
        """
        blob = TextBlob(text)
        
        return {
            "word_count": len(blob.words),
            "sentence_count": len(blob.sentences),
            "char_count": len(text)
        }
    
    def analyze_full_document(self, text: str, keyword_limit: int = 10) -> Dict[str, Any]:
        """
        Perform complete analysis of a document
        """
        sentiment = self.analyze_sentiment(text)
        keywords = self.extract_keywords(text, keyword_limit)
        readability = self.calculate_readability(text)
        stats = self.get_basic_stats(text)
        
        return {
            "sentiment": sentiment,
            "keywords": keywords,
            "readability": readability,
            "stats": stats
        }


# Global analyzer instance
analyzer = TextAnalyzer() 