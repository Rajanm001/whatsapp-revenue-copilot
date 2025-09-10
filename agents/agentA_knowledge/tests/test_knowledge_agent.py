"""
Unit tests for Agent A - Knowledge Agent
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from graph import KnowledgeAgent, IngestionResult, KnowledgeAnswer

class TestKnowledgeAgent:
    
    @pytest.fixture
    def agent(self):
        """Create test agent instance"""
        with patch('graph.chromadb.PersistentClient'):
            with patch('graph.OpenAIEmbeddings'):
                with patch('graph.ChatOpenAI'):
                    return KnowledgeAgent()
    
    def test_ingest_document_success(self, agent):
        """Test successful document ingestion"""
        with patch.object(agent, 'graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "chunks": [Mock(), Mock(), Mock()],
                "error": None
            }
            
            result = agent.ingest("test-file-id")
            
            assert isinstance(result, IngestionResult)
            assert result.chunks == 3
            assert result.request_id is not None
    
    def test_ingest_document_failure(self, agent):
        """Test document ingestion failure"""
        with patch.object(agent, 'graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "chunks": [],
                "error": "Failed to process document"
            }
            
            with pytest.raises(Exception, match="Failed to process document"):
                agent.ingest("test-file-id")
    
    def test_ask_question_success(self, agent):
        """Test successful Q&A"""
        with patch.object(agent, 'graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "answer": "Test answer",
                "citations": [],
                "confidence": 0.8,
                "error": None
            }
            
            result = agent.ask("user123", "What is the refund policy?")
            
            assert isinstance(result, KnowledgeAnswer)
            assert result.answer == "Test answer"
            assert result.confidence == 0.8
            assert result.request_id is not None
    
    def test_ask_question_failure(self, agent):
        """Test Q&A failure"""
        with patch.object(agent, 'graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "answer": "",
                "citations": [],
                "confidence": 0.0,
                "error": "No relevant documents found"
            }
            
            with pytest.raises(Exception, match="No relevant documents found"):
                agent.ask("user123", "What is the refund policy?")
    
    def test_parse_scheduling_info(self, agent):
        """Test scheduling information parsing"""
        # Mock the _extract_time_info method
        with patch.object(agent, '_extract_time_info') as mock_extract:
            mock_extract.return_value = {
                'time': ['10:00'],
                'day': ['tuesday'],
                'with': ['Dana']
            }
            
            with patch.object(agent, '_parse_datetime') as mock_parse_dt:
                from datetime import datetime
                mock_parse_dt.return_value = datetime(2024, 1, 1, 10, 0)
                
                result = agent.followup_parse("Schedule a call next Tuesday at 10:00 with Dana")
                
                assert result.title is not None
                assert "2024-01-01T10:00:00" in result.start_iso

if __name__ == "__main__":
    pytest.main([__file__])
