"""
Feedback System Module

Provides user feedback collection and relevance refinement capabilities.
Allows users to rate results and uses feedback to improve future queries.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict
from threading import Lock


class FeedbackStore:
    """
    Store and manage user feedback on query results.
    
    Feedback is stored in-memory with optional persistence to file.
    Used to track result quality and enable relevance refinement.
    """
    
    def __init__(self, storage_file: str = "feedback_data.json"):
        """
        Initialize feedback store.
        
        Args:
            storage_file: Path to JSON file for persistent storage
        """
        self.storage_file = storage_file
        self._feedback = defaultdict(list)  # query -> [feedback_entries]
        self._lock = Lock()
        
        # Load existing feedback if available
        self._load()
    
    def add_feedback(
        self,
        query: str,
        result_sequence: str,
        rating: int,
        user_id: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Dict:
        """
        Add user feedback for a query result.
        
        Args:
            query: The original query string
            result_sequence: The result sequence being rated
            rating: Rating from 1 (poor) to 5 (excellent)
            user_id: Optional user identifier
            comment: Optional text comment
            
        Returns:
            Dictionary with feedback entry details
            
        Raises:
            ValueError: If rating is not in range 1-5
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'result_sequence': result_sequence,
            'rating': rating,
            'user_id': user_id,
            'comment': comment,
        }
        
        with self._lock:
            self._feedback[query].append(feedback_entry)
            self._save()
        
        return feedback_entry
    
    def get_feedback_for_query(self, query: str) -> List[Dict]:
        """
        Get all feedback entries for a specific query.
        
        Args:
            query: The query to retrieve feedback for
            
        Returns:
            List of feedback dictionaries
        """
        with self._lock:
            return list(self._feedback.get(query, []))
    
    def get_average_rating(self, query: str) -> Optional[float]:
        """
        Calculate average rating for a query.
        
        Args:
            query: The query to calculate rating for
            
        Returns:
            Average rating (1.0-5.0) or None if no feedback exists
        """
        feedback_list = self.get_feedback_for_query(query)
        
        if not feedback_list:
            return None
        
        ratings = [f['rating'] for f in feedback_list]
        return sum(ratings) / len(ratings)
    
    def get_top_rated_results(self, query: str, min_rating: float = 4.0) -> List[str]:
        """
        Get result sequences with high ratings for a query.
        
        Args:
            query: The query to get top results for
            min_rating: Minimum average rating threshold
            
        Returns:
            List of highly-rated result sequences
        """
        feedback_list = self.get_feedback_for_query(query)
        
        # Group by result sequence
        sequence_ratings = defaultdict(list)
        for entry in feedback_list:
            sequence_ratings[entry['result_sequence']].append(entry['rating'])
        
        # Calculate averages and filter
        top_results = []
        for sequence, ratings in sequence_ratings.items():
            avg_rating = sum(ratings) / len(ratings)
            if avg_rating >= min_rating:
                top_results.append(sequence)
        
        return top_results
    
    def get_statistics(self) -> Dict:
        """
        Get overall feedback statistics.
        
        Returns:
            Dictionary with:
                - total_feedback: Total number of feedback entries
                - unique_queries: Number of unique queries with feedback
                - average_rating: Overall average rating
                - rating_distribution: Count of each rating (1-5)
        """
        with self._lock:
            all_feedback = []
            for entries in self._feedback.values():
                all_feedback.extend(entries)
            
            if not all_feedback:
                return {
                    'total_feedback': 0,
                    'unique_queries': 0,
                    'average_rating': 0.0,
                    'rating_distribution': {i: 0 for i in range(1, 6)},
                }
            
            ratings = [f['rating'] for f in all_feedback]
            rating_counts = {i: ratings.count(i) for i in range(1, 6)}
            
            return {
                'total_feedback': len(all_feedback),
                'unique_queries': len(self._feedback),
                'average_rating': sum(ratings) / len(ratings),
                'rating_distribution': rating_counts,
            }
    
    def _save(self):
        """Save feedback to file (thread-safe)."""
        try:
            with open(self.storage_file, 'w') as f:
                # Convert defaultdict to regular dict for JSON serialization
                data = {k: v for k, v in self._feedback.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            # Log error but don't crash
            print(f"Warning: Could not save feedback to {self.storage_file}: {e}")
    
    def _load(self):
        """Load feedback from file if it exists."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self._feedback = defaultdict(list, data)
            except Exception as e:
                print(f"Warning: Could not load feedback from {self.storage_file}: {e}")


# Global feedback store instance
_feedback_store = FeedbackStore()


def get_feedback_store() -> FeedbackStore:
    """Get the global feedback store instance."""
    return _feedback_store


def suggest_similar_queries(query: str, max_suggestions: int = 5) -> List[Dict]:
    """
    Suggest similar queries based on feedback history.
    
    Finds queries with similar patterns that have high ratings,
    useful for query refinement and discovery.
    
    Args:
        query: The current query
        max_suggestions: Maximum number of suggestions to return
        
    Returns:
        List of dictionaries with:
            - suggested_query: The suggested query string
            - average_rating: Average rating for that query
            - feedback_count: Number of feedback entries
    """
    store = get_feedback_store()
    suggestions = []
    
    # Normalize query for comparison
    query_words = set(query.upper().split())
    
    # Get all queries with feedback
    all_queries = list(store._feedback.keys())
    
    for other_query in all_queries:
        if other_query.upper() == query.upper():
            continue  # Skip exact match
        
        # Calculate word overlap
        other_words = set(other_query.upper().split())
        overlap = len(query_words & other_words)
        
        if overlap > 0:  # Has some similarity
            avg_rating = store.get_average_rating(other_query)
            feedback_count = len(store.get_feedback_for_query(other_query))
            
            suggestions.append({
                'suggested_query': other_query,
                'average_rating': avg_rating,
                'feedback_count': feedback_count,
                'word_overlap': overlap,
            })
    
    # Sort by rating first, then by overlap
    suggestions.sort(
        key=lambda x: (x['average_rating'], x['word_overlap']),
        reverse=True
    )
    
    return suggestions[:max_suggestions]


def analyze_query_performance(query: str) -> Dict:
    """
    Analyze performance of a query based on feedback.
    
    Args:
        query: The query to analyze
        
    Returns:
        Dictionary with performance metrics:
            - average_rating: Average user rating
            - total_feedback: Total feedback count
            - positive_ratio: Percentage of ratings >= 4
            - top_rated_results: Number of highly-rated results
            - suggestions: List of suggested improvements
    """
    store = get_feedback_store()
    feedback_list = store.get_feedback_for_query(query)
    
    if not feedback_list:
        return {
            'query': query,
            'average_rating': None,
            'total_feedback': 0,
            'positive_ratio': 0.0,
            'top_rated_results': 0,
            'suggestions': suggest_similar_queries(query),
        }
    
    ratings = [f['rating'] for f in feedback_list]
    positive_count = sum(1 for r in ratings if r >= 4)
    
    return {
        'query': query,
        'average_rating': sum(ratings) / len(ratings),
        'total_feedback': len(feedback_list),
        'positive_ratio': positive_count / len(ratings) * 100,
        'top_rated_results': len(store.get_top_rated_results(query)),
        'suggestions': suggest_similar_queries(query),
    }
