"""
Intent Classifier API
Standalone service for classifying WhatsApp message intents
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from intent_classifier import classify_intent, IntentClassification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Intent Classifier API",
    description="Classifies WhatsApp message intents for routing",
    version="1.0.0"
)

# Request/Response Models
class ClassifyRequest(BaseModel):
    message: str
    has_attachments: bool = False
    context: Optional[str] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "intent-classifier"}

# Intent classification endpoint
@app.post("/classify", response_model=IntentClassification)
async def classify_message(request: ClassifyRequest) -> IntentClassification:
    """
    Classify intent of WhatsApp message
    
    Args:
        request: Contains message text, attachment info, and context
        
    Returns:
        IntentClassification with intent and extracted entities
    """
    try:
        logger.info(f"Classifying message: {request.message[:100]}...")
        result = classify_intent(
            request.message, 
            request.has_attachments, 
            request.context
        )
        logger.info(f"Classified as: {result.intent} (confidence: {result.confidence})")
        return result
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
