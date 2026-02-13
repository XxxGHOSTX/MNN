"""
Unit tests for Relational Buffer
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from buffer.relational_buffer import RelationalBuffer, DatabaseSchema


class TestDatabaseSchema(unittest.TestCase):
    """Test cases for Database Schema."""
    
    def test_manifold_coordinates_schema(self):
        """Test manifold_coordinates table schema."""
        schema = DatabaseSchema.MANIFOLD_COORDINATES_TABLE
        
        self.assertIn("CREATE TABLE", schema)
        self.assertIn("manifold_coordinates", schema)
        self.assertIn("query_text", schema)
        self.assertIn("response_text", schema)
        self.assertIn("confidence_score", schema)
    
    def test_void_logs_schema(self):
        """Test void_logs table schema."""
        schema = DatabaseSchema.VOID_LOGS_TABLE
        
        self.assertIn("CREATE TABLE", schema)
        self.assertIn("void_logs", schema)
        self.assertIn("query_text", schema)
        self.assertIn("failure_reason", schema)
        self.assertIn("void_type", schema)
    
    def test_get_all_schemas(self):
        """Test getting all schemas."""
        all_schemas = DatabaseSchema.get_all_schemas()
        
        self.assertIn("manifold_coordinates", all_schemas)
        self.assertIn("void_logs", all_schemas)


class TestRelationalBuffer(unittest.TestCase):
    """Test cases for Relational Buffer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.buffer = RelationalBuffer()
        self.buffer.connect()
    
    def test_connection(self):
        """Test database connection."""
        self.assertTrue(self.buffer.connected)
    
    def test_store_successful_resolution(self):
        """Test storing successful resolution."""
        self.buffer.store_successful_resolution(
            query="test query",
            response="test response",
            confidence=0.95,
            hardware_id_hash="test_hash"
        )
        
        self.assertEqual(len(self.buffer.manifold_coordinates), 1)
        
        entry = self.buffer.manifold_coordinates[0]
        self.assertEqual(entry["query_text"], "test query")
        self.assertEqual(entry["response_text"], "test response")
        self.assertEqual(entry["confidence_score"], 0.95)
    
    def test_store_void_log(self):
        """Test storing void log."""
        self.buffer.store_void_log(
            query="failed query",
            failure_reason="Low confidence",
            confidence=0.1,
            void_type="noise"
        )
        
        self.assertEqual(len(self.buffer.void_logs), 1)
        
        entry = self.buffer.void_logs[0]
        self.assertEqual(entry["query_text"], "failed query")
        self.assertEqual(entry["failure_reason"], "Low confidence")
        self.assertEqual(entry["void_type"], "noise")
    
    def test_get_successful_resolutions(self):
        """Test retrieving successful resolutions."""
        # Store multiple resolutions
        self.buffer.store_successful_resolution("q1", "r1", 0.9)
        self.buffer.store_successful_resolution("q2", "r2", 0.7)
        self.buffer.store_successful_resolution("q3", "r3", 0.5)
        
        # Get all above threshold
        results = self.buffer.get_successful_resolutions(min_confidence=0.6)
        self.assertEqual(len(results), 2)
        
        # Check sorting (highest confidence first)
        self.assertEqual(results[0]["confidence_score"], 0.9)
        self.assertEqual(results[1]["confidence_score"], 0.7)
    
    def test_get_void_logs(self):
        """Test retrieving void logs."""
        # Store multiple void logs
        self.buffer.store_void_log("q1", "reason1", void_type="noise")
        self.buffer.store_void_log("q2", "reason2", void_type="gap")
        self.buffer.store_void_log("q3", "reason3", void_type="noise")
        
        # Get all void logs
        all_logs = self.buffer.get_void_logs()
        self.assertEqual(len(all_logs), 3)
        
        # Get filtered by type
        noise_logs = self.buffer.get_void_logs(void_type="noise")
        self.assertEqual(len(noise_logs), 2)
    
    def test_analyze_knowledge_gaps(self):
        """Test knowledge gap analysis."""
        # Store mixed data
        self.buffer.store_successful_resolution("q1", "r1", 0.9)
        self.buffer.store_successful_resolution("q2", "r2", 0.8)
        self.buffer.store_void_log("q3", "reason", void_type="noise")
        self.buffer.store_void_log("q4", "reason", void_type="gap")
        
        analysis = self.buffer.analyze_knowledge_gaps()
        
        self.assertEqual(analysis["total_successful_resolutions"], 2)
        self.assertEqual(analysis["total_void_logs"], 2)
        self.assertIn("void_type_distribution", analysis)
        self.assertIn("success_rate", analysis)
        
        # Check void type counts
        self.assertEqual(analysis["void_type_distribution"]["noise"], 1)
        self.assertEqual(analysis["void_type_distribution"]["gap"], 1)
    
    def test_get_schema_sql(self):
        """Test getting schema SQL."""
        schema_sql = self.buffer.get_schema_sql()
        
        self.assertIn("manifold_coordinates", schema_sql)
        self.assertIn("void_logs", schema_sql)


if __name__ == '__main__':
    unittest.main()
