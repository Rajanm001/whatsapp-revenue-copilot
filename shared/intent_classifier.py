"""
Shared Intent Classifier for WhatsApp messages
Routes messages to appropriate agents based on content analysis
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain.schema import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
import re
import uuid

class ExtractedEntities(BaseModel):
    """Entities extracted from user message"""
    names: List[str] = Field(default=[], description="Person names mentioned")
    organizations: List[str] = Field(default=[], description="Company/organization names")
    dates_times: List[str] = Field(default=[], description="Date/time mentions")
    budget_amounts: List[str] = Field(default=[], description="Budget or money amounts")
    contact_info: List[str] = Field(default=[], description="Emails, phones, etc.")

class IntentClassification(BaseModel):
    """Intent classification result"""
    intent: str = Field(
        description="Primary intent",
        enum=["knowledge_qa", "lead_capture", "proposal_request", "next_step", "status_update", "smalltalk", "unknown"]
    )
    confidence: float = Field(description="Confidence score 0-1")
    entities: ExtractedEntities = Field(description="Extracted entities")
    reasoning: str = Field(description="Brief reasoning for classification")

class IntentClassifier:
    """Lightweight intent classifier for routing WhatsApp messages"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=500
        )
        self.parser = PydanticOutputParser(pydantic_object=IntentClassification)
    
    def classify(self, message: str, has_attachments: bool = False, context: Optional[str] = None) -> IntentClassification:
        """
        Classify intent of WhatsApp message
        
        Args:
            message: The user's message text
            has_attachments: Whether message includes file attachments
            context: Previous conversation context if available
            
        Returns:
            IntentClassification with intent and extracted entities
        """
        # Quick pre-routing for attachments
        if has_attachments:
            return IntentClassification(
                intent="knowledge_qa",
                confidence=0.9,
                entities=ExtractedEntities(),
                reasoning="Message contains file attachments - routing for ingestion"
            )
        
        # Build prompt for LLM classification
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(message, context)
        
        # Get LLM response
        messages = [
            HumanMessage(content=f"{system_prompt}\n\n{user_prompt}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            result = self.parser.parse(response.content)
            return result
        except Exception as e:
            # Fallback classification
            return IntentClassification(
                intent="unknown",
                confidence=0.1,
                entities=ExtractedEntities(),
                reasoning=f"Classification failed: {str(e)}"
            )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for intent classification"""
        return """You are an expert intent classifier for a WhatsApp business copilot.

Analyze messages and classify them into these intents:

1. **knowledge_qa**: Questions about company info, policies, docs (e.g., "What's our refund policy?")
2. **lead_capture**: New prospect information (e.g., "John from Acme wants a PoC, budget 10k")
3. **proposal_request**: Request to generate proposals (e.g., "Draft a proposal for Acme")
4. **next_step**: Scheduling meetings/calls (e.g., "Schedule demo next Wed at 11")
5. **status_update**: Deal status changes (e.g., "We lost Acme - budget cut")
6. **smalltalk**: Greetings, thanks, casual conversation
7. **unknown**: Unclear or unrelated messages

Extract entities like names, companies, dates, budgets, contact info.

CRITICAL: Return only valid JSON matching the schema. No explanatory text."""

    def _build_user_prompt(self, message: str, context: Optional[str] = None) -> str:
        """Build user prompt with message and context"""
        prompt = f"Message to classify: \"{message}\"\n"
        
        if context:
            prompt += f"Previous context: {context}\n"
        
        prompt += f"\nReturn classification as JSON:\n{self.parser.get_format_instructions()}"
        
        return prompt
    
    def extract_scheduling_hints(self, message: str) -> Dict[str, Any]:
        """Extract scheduling-related information from message"""
        patterns = {
            'days': r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b',
            'times': r'\b(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?\b',
            'dates': r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))\b',
            'relative': r'\b(today|tomorrow|next week|this week)\b'
        }
        
        extracted = {}
        for key, pattern in patterns.items():
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                extracted[key] = matches
        
        return extracted

# Global classifier instance
classifier = IntentClassifier()

def classify_intent(message: str, has_attachments: bool = False, context: Optional[str] = None) -> IntentClassification:
    """Convenience function for intent classification"""
    return classifier.classify(message, has_attachments, context)
