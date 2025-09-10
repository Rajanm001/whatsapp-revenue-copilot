"""
FastAPI application for Agent B - Dealflow Agent
Provides REST endpoints for lead management and proposal generation
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from graph import dealflow_agent, Lead, ProposalCopy, NextStepSchedule, StatusClassification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dealflow Agent API",
    description="Agent B - Handles lead capture, proposal generation, and dealflow management",
    version="1.0.0"
)

# Request/Response Models
class NewLeadRequest(BaseModel):
    raw: str

class ProposalRequest(BaseModel):
    lead: Dict[str, Any]

class NextStepRequest(BaseModel):
    text: str

class StatusRequest(BaseModel):
    label: str
    reason_text: Optional[str] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "dealflow"}

# Lead capture endpoint
@app.post("/agentB/newlead", response_model=Lead)
async def capture_lead(request: NewLeadRequest) -> Lead:
    """
    Parse and enrich new lead information
    
    Args:
        request: Contains raw text with lead information
        
    Returns:
        Lead with parsed and enriched data
    """
    try:
        logger.info(f"Capturing lead from: {request.raw[:100]}...")
        result = dealflow_agent.newlead(request.raw)
        logger.info(f"Captured lead: {result.name} from {result.company}")
        return result
    except Exception as e:
        logger.error(f"Lead capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Proposal generation endpoint
@app.post("/agentB/proposal-copy", response_model=ProposalCopy)
async def generate_proposal(request: ProposalRequest) -> ProposalCopy:
    """
    Generate proposal content for a lead
    
    Args:
        request: Contains lead information
        
    Returns:
        ProposalCopy with generated content
    """
    try:
        logger.info(f"Generating proposal for: {request.lead.get('company', 'Unknown')}")
        result = dealflow_agent.proposal_copy(request.lead)
        logger.info(f"Generated proposal: {result.title}")
        return result
    except Exception as e:
        logger.error(f"Proposal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Next step scheduling endpoint
@app.post("/agentB/nextstep-parse", response_model=NextStepSchedule)
async def parse_next_step(request: NextStepRequest) -> NextStepSchedule:
    """
    Parse scheduling information for next steps
    
    Args:
        request: Contains text with scheduling intent
        
    Returns:
        NextStepSchedule with parsed scheduling info
    """
    try:
        logger.info(f"Parsing next step: {request.text}")
        result = dealflow_agent.nextstep_parse(request.text)
        logger.info(f"Parsed next step: {result.title} at {result.start_iso}")
        return result
    except Exception as e:
        logger.error(f"Next step parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Status classification endpoint
@app.post("/agentB/status-classify", response_model=StatusClassification)
async def classify_status(request: StatusRequest) -> StatusClassification:
    """
    Classify deal status and reason
    
    Args:
        request: Contains status label and optional reason text
        
    Returns:
        StatusClassification with categorized status
    """
    try:
        logger.info(f"Classifying status: {request.label}")
        result = dealflow_agent.status_classify(request.label, request.reason_text)
        logger.info(f"Classified as: {result.label} - {result.reason_category}")
        return result
    except Exception as e:
        logger.error(f"Status classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
