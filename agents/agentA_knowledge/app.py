"""
FastAPI application for Agent A - Knowledge Agent
Provides REST endpoints for document ingestion and Q&A
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from graph import knowledge_agent, IngestionResult, KnowledgeAnswer, FollowUpSchedule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Knowledge Agent API",
    description="Agent A - Handles document ingestion, Q&A with citations, and follow-up scheduling",
    version="1.0.0"
)

# Request/Response Models
class IngestRequest(BaseModel):
    drive_file_id: str

class AskRequest(BaseModel):
    user_id: str
    text: str

class FollowUpRequest(BaseModel):
    text: str

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "knowledge"}

# Document ingestion endpoint
@app.post("/agentA/ingest", response_model=IngestionResult)
async def ingest_document(request: IngestRequest) -> IngestionResult:
    """
    Ingest a document from Google Drive
    
    Args:
        request: Contains drive_file_id
        
    Returns:
        IngestionResult with chunks and token count
    """
    try:
        logger.info(f"Ingesting document: {request.drive_file_id}")
        result = knowledge_agent.ingest(request.drive_file_id)
        logger.info(f"Successfully ingested {result.chunks} chunks")
        return result
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Q&A endpoint
@app.post("/agentA/ask", response_model=KnowledgeAnswer)
async def ask_question(request: AskRequest) -> KnowledgeAnswer:
    """
    Answer a question with grounded response and citations
    
    Args:
        request: Contains user_id and question text
        
    Returns:
        KnowledgeAnswer with answer, citations, and confidence
    """
    try:
        logger.info(f"Processing question for user {request.user_id}: {request.text}")
        result = knowledge_agent.ask(request.user_id, request.text)
        logger.info(f"Generated answer with confidence: {result.confidence}")
        return result
    except Exception as e:
        logger.error(f"Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Follow-up scheduling endpoint  
@app.post("/agentA/followup-parse", response_model=FollowUpSchedule)
async def parse_followup(request: FollowUpRequest) -> FollowUpSchedule:
    """
    Parse scheduling information from natural language
    
    Args:
        request: Contains text with scheduling intent
        
    Returns:
        FollowUpSchedule with parsed time and details
    """
    try:
        logger.info(f"Parsing scheduling info: {request.text}")
        result = knowledge_agent.followup_parse(request.text)
        logger.info(f"Parsed meeting: {result.title} at {result.start_iso}")
        return result
    except Exception as e:
        logger.error(f"Scheduling parse failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
