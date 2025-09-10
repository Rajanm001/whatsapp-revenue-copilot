"""
Unit tests for Agent B - Dealflow Agent
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from graph import DealflowAgent, Lead, ProposalCopy

class TestDealflowAgent:
    
    @pytest.fixture
    def agent(self):
        """Create test agent instance"""
        with patch('graph.ChatOpenAI'):
            return DealflowAgent()
    
    def test_lead_capture_success(self, agent):
        """Test successful lead capture"""
        with patch.object(agent, 'graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "enriched_lead": {
                    "name": "John Smith",
                    "company": "Acme Corp",
                    "intent": "PoC request",
                    "budget": "10k",
                    "normalized_company_domain": "acme.com",
                    "quality_score": 0.8,
                    "request_id": "test-123"
                },
                "error": None
            }
            
            result = agent.newlead("John from Acme wants a PoC, budget around 10k")
            
            assert isinstance(result, Lead)
            assert result.name == "John Smith"
            assert result.company == "Acme Corp"
            assert result.quality_score == 0.8
    
    def test_proposal_generation(self, agent):
        """Test proposal generation"""
        with patch.object(agent, '_generate_proposal') as mock_generate:
            mock_generate.return_value = {
                "proposal_content": {
                    "title": "Custom Business Proposal for Acme Corp",
                    "summary_blurb": "We propose to deliver...",
                    "bullet_points": ["Point 1", "Point 2", "Point 3"],
                    "request_id": "test-123"
                },
                "error": None
            }
            
            lead_data = {"name": "John", "company": "Acme", "intent": "PoC"}
            result = agent.proposal_copy(lead_data)
            
            assert isinstance(result, ProposalCopy)
            assert "Acme Corp" in result.title
            assert len(result.bullet_points) == 3
    
    def test_company_domain_guessing(self, agent):
        """Test company domain guessing logic"""
        # Test normal company name
        domain = agent._guess_company_domain("Acme Corporation")
        assert domain == "acme.com"
        
        # Test company with spaces
        domain = agent._guess_company_domain("Big Tech Inc")
        assert domain == "bigtech.com"
        
        # Test empty company
        domain = agent._guess_company_domain("")
        assert domain is None
    
    def test_lead_quality_scoring(self, agent):
        """Test lead quality scoring"""
        # Complete lead
        complete_lead = {
            "name": "John Smith",
            "company": "Acme Corp",
            "intent": "PoC request", 
            "budget": "10k"
        }
        score = agent._calculate_quality_score(complete_lead)
        assert score == 1.0
        
        # Partial lead
        partial_lead = {
            "name": "John Smith",
            "company": "Acme Corp"
        }
        score = agent._calculate_quality_score(partial_lead)
        assert score == 0.5
        
        # Empty lead
        empty_lead = {}
        score = agent._calculate_quality_score(empty_lead)
        assert score == 0.0
    
    def test_datetime_parsing(self, agent):
        """Test datetime parsing from natural language"""
        # Test "tomorrow" parsing
        result = agent._parse_datetime_from_text("Let's meet tomorrow at 2pm")
        assert result is not None
        assert result.hour == 14  # 2pm
        
        # Test "next week" parsing
        result = agent._parse_datetime_from_text("Schedule for next week at 10:30am")
        assert result is not None
        assert result.hour == 10
        assert result.minute == 30

if __name__ == "__main__":
    pytest.main([__file__])
