"""
WhatsApp Sales Agent - By Rajan  
Smart sales automation for WhatsApp conversations.
Captures leads, generates proposals, and manages the entire sales pipeline.
"""

from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
import uuid
from datetime import datetime, timedelta
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Lead(BaseModel):
    """Lead information model"""
    name: str = Field(description="Contact name")
    company: str = Field(description="Company name")
    intent: str = Field(description="Business intent/requirement")
    budget: Optional[str] = Field(default=None, description="Budget information")
    normalized_company_domain: Optional[str] = Field(default=None, description="Guessed company domain")
    quality_score: Optional[float] = Field(default=None, description="Lead quality score 0-1")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    request_id: str = Field(description="Request tracking ID")

class ProposalCopy(BaseModel):
    """Generated proposal content"""
    title: str = Field(description="Proposal title")
    summary_blurb: str = Field(description="Executive summary")
    bullet_points: List[str] = Field(description="Key proposal points")
    request_id: str = Field(description="Request tracking ID")

class NextStepSchedule(BaseModel):
    """Parsed next step scheduling"""
    title: str = Field(description="Meeting/task title")
    start_iso: str = Field(description="Start time in ISO format")
    end_iso: Optional[str] = Field(description="End time in ISO format")
    request_id: str = Field(description="Request tracking ID")

class StatusClassification(BaseModel):
    """Deal status classification"""
    label: str = Field(description="Status label", enum=["Won", "Lost", "On hold"])
    reason_category: str = Field(description="Categorized reason")
    reason_summary: str = Field(description="Summary of reason")
    request_id: str = Field(description="Request tracking ID")

class DealflowState(TypedDict):
    """State for dealflow agent graph"""
    raw_text: str
    request_id: str
    parsed_lead: Optional[Dict[str, Any]]
    enriched_lead: Optional[Dict[str, Any]]
    proposal_content: Optional[Dict[str, Any]]
    schedule_info: Optional[Dict[str, Any]]
    status_info: Optional[Dict[str, Any]]
    error: Optional[str]

class DealflowAgent:
    """LangGraph agent for dealflow management"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=1000
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(DealflowState)
        
        # Add nodes
        workflow.add_node("parse_lead_node", self._parse_lead)
        workflow.add_node("enrich_lead_node", self._enrich_lead)
        workflow.add_node("generate_proposal_node", self._generate_proposal)
        workflow.add_node("parse_schedule_node", self._parse_schedule)
        workflow.add_node("classify_status_node", self._classify_status)
        
        # Entry point based on operation type
        workflow.set_entry_point("parse_lead_node")
        
        # Simple linear flow for now - could be made more sophisticated
        workflow.add_edge("parse_lead_node", "enrich_lead_node")
        workflow.add_edge("enrich_lead_node", END)
        workflow.add_edge("generate_proposal_node", END)
        workflow.add_edge("parse_schedule_node", END)
        workflow.add_edge("classify_status_node", END)
        
        return workflow.compile()
    
    def _parse_lead(self, state: DealflowState) -> DealflowState:
        """Parse lead information from raw text"""
        try:
            raw_text = state.get("raw_text", "")
            
            parse_prompt = f"""Extract lead information from this text:
            
"{raw_text}"

Extract:
- Contact name
- Company name  
- Business intent/requirement
- Budget information (if mentioned)
- Any other relevant details

Return as structured JSON with fields: name, company, intent, budget, notes"""

            response = self.llm.invoke(parse_prompt)
            
            # Simple JSON parsing (in production, use structured output)
            try:
                import json
                parsed_data = json.loads(response.content)
            except:
                # Fallback manual parsing
                parsed_data = self._manual_parse_lead(raw_text)
            
            state["parsed_lead"] = parsed_data
            logger.info(f"Parsed lead: {parsed_data.get('name')} from {parsed_data.get('company')}")
            
        except Exception as e:
            logger.error(f"Lead parsing error: {e}")
            state["error"] = str(e)
        
        return state
    
    def _enrich_lead(self, state: DealflowState) -> DealflowState:
        """Enrich lead with additional data"""
        try:
            parsed_lead = state.get("parsed_lead", {})
            if not parsed_lead:
                return state
            
            company = parsed_lead.get("company", "")
            
            # Simple domain guessing
            domain_guess = self._guess_company_domain(company)
            
            # Simple quality scoring
            quality_score = self._calculate_quality_score(parsed_lead)
            
            enriched = {
                **parsed_lead,
                "normalized_company_domain": domain_guess,
                "quality_score": quality_score,
                "request_id": state["request_id"]
            }
            
            state["enriched_lead"] = enriched
            logger.info(f"Enriched lead with domain: {domain_guess}, quality: {quality_score}")
            
        except Exception as e:
            logger.error(f"Lead enrichment error: {e}")
            state["error"] = str(e)
        
        return state
    
    def _generate_proposal(self, state: DealflowState) -> DealflowState:
        """Generate proposal content"""
        try:
            lead_data = state.get("parsed_lead", {})
            if not lead_data:
                return {**state, "error": "No lead data for proposal generation"}
            
            proposal_prompt = f"""Generate a professional business proposal for:

Company: {lead_data.get('company', 'Unknown')}
Contact: {lead_data.get('name', 'Unknown')}
Requirement: {lead_data.get('intent', 'General business needs')}
Budget: {lead_data.get('budget', 'To be discussed')}

Generate:
1. A compelling title
2. A 120-160 word executive summary
3. 3-5 key bullet points highlighting our value proposition

Keep the tone professional but engaging. Focus on solving their specific needs."""

            response = self.llm.invoke(proposal_prompt)
            
            # Parse the response (simplified)
            content = response.content
            lines = content.split('\n')
            
            title = "Custom Business Proposal"
            summary = ""
            bullets = []
            
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if "title" in line.lower() or line.startswith("1."):
                    current_section = "title"
                    title = line.split(":", 1)[-1].strip() if ":" in line else line
                elif "summary" in line.lower() or line.startswith("2."):
                    current_section = "summary"
                elif "bullet" in line.lower() or "point" in line.lower() or line.startswith("3."):
                    current_section = "bullets"
                elif current_section == "summary" and not line.startswith("-"):
                    summary += line + " "
                elif current_section == "bullets" and (line.startswith("-") or line.startswith("•")):
                    bullets.append(line.lstrip("-• "))
            
            proposal_content = {
                "title": title[:100],  # Limit length
                "summary_blurb": summary[:500],  # Limit length
                "bullet_points": bullets[:5],  # Limit to 5 bullets
                "request_id": state["request_id"]
            }
            
            state["proposal_content"] = proposal_content
            logger.info(f"Generated proposal: {title}")
            
        except Exception as e:
            logger.error(f"Proposal generation error: {e}")
            state["error"] = str(e)
        
        return state
    
    def _parse_schedule(self, state: DealflowState) -> DealflowState:
        """Parse scheduling information"""
        try:
            raw_text = state.get("raw_text", "")
            
            # Extract time-related information
            time_patterns = {
                'day': r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today|next\s+\w+day)\b',
                'time': r'\b(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?\b',
                'date': r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
                'meeting_type': r'\b(demo|call|meeting|presentation|review)\b'
            }
            
            extracted = {}
            for key, pattern in time_patterns.items():
                matches = re.findall(pattern, raw_text, re.IGNORECASE)
                if matches:
                    extracted[key] = matches[0] if isinstance(matches[0], str) else matches[0][0]
            
            # Generate meeting title
            meeting_type = extracted.get('meeting_type', 'meeting')
            title = f"Business {meeting_type}"
            
            # Parse datetime (simplified)
            start_time = self._parse_datetime_from_text(raw_text)
            end_time = start_time + timedelta(hours=1) if start_time else None
            
            schedule_info = {
                "title": title,
                "start_iso": start_time.isoformat() if start_time else datetime.now().isoformat(),
                "end_iso": end_time.isoformat() if end_time else None,
                "request_id": state["request_id"]
            }
            
            state["schedule_info"] = schedule_info
            logger.info(f"Parsed scheduling: {title} at {start_time}")
            
        except Exception as e:
            logger.error(f"Schedule parsing error: {e}")
            state["error"] = str(e)
        
        return state
    
    def _classify_status(self, state: DealflowState) -> DealflowState:
        """Classify deal status and reason"""
        try:
            raw_text = state.get("raw_text", "")
            
            classify_prompt = f"""Classify this deal status update:

"{raw_text}"

Determine:
1. Status label: Won, Lost, or On hold
2. Reason category: budget, timeline, competition, internal, technical, other
3. Brief reason summary (1-2 sentences)

Return structured classification."""

            response = self.llm.invoke(classify_prompt)
            
            # Simple parsing (in production, use structured output)
            content = response.content.lower()
            
            if "won" in content:
                label = "Won"
            elif "lost" in content:
                label = "Lost"  
            else:
                label = "On hold"
            
            # Categorize reason
            reason_categories = {
                "budget": ["budget", "cost", "price", "money", "expensive"],
                "timeline": ["timeline", "schedule", "time", "deadline", "urgent"],
                "competition": ["competitor", "competition", "alternative", "other vendor"],
                "internal": ["internal", "approval", "decision", "team", "management"],
                "technical": ["technical", "requirement", "feature", "integration"],
            }
            
            reason_category = "other"
            for category, keywords in reason_categories.items():
                if any(keyword in content for keyword in keywords):
                    reason_category = category
                    break
            
            status_info = {
                "label": label,
                "reason_category": reason_category,
                "reason_summary": raw_text[:200],  # First 200 chars
                "request_id": state["request_id"]
            }
            
            state["status_info"] = status_info
            logger.info(f"Classified status: {label} - {reason_category}")
            
        except Exception as e:
            logger.error(f"Status classification error: {e}")
            state["error"] = str(e)
        
        return state
    
    def _manual_parse_lead(self, text: str) -> Dict[str, Any]:
        """Fallback manual lead parsing"""
        # Simple regex-based parsing
        patterns = {
            'name': r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            'company': r'\b(?:from|at)\s+([A-Z][a-zA-Z\s&]+?)(?:\s|$)',
            'budget': r'\$?(\d+[kK]?|\d+,?\d*)',
            'intent': r'\b(PoC|proof of concept|demo|trial|project|solution)\b'
        }
        
        parsed = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed[key] = match.group(1).strip()
        
        return parsed
    
    def _guess_company_domain(self, company: str) -> Optional[str]:
        """Simple company domain guessing"""
        if not company:
            return None
        
        # Remove common corporate suffixes
        clean_name = re.sub(r'\b(inc|llc|ltd|corp|corporation)\b', '', company.lower()).strip()
        
        # Replace spaces and special chars
        domain_candidate = re.sub(r'[^a-z0-9]', '', clean_name)
        
        return f"{domain_candidate}.com" if domain_candidate else None
    
    def _calculate_quality_score(self, lead_data: Dict[str, Any]) -> float:
        """Simple lead quality scoring"""
        score = 0.0
        
        # Has name
        if lead_data.get("name"):
            score += 0.2
        
        # Has company
        if lead_data.get("company"):
            score += 0.3
        
        # Has clear intent
        if lead_data.get("intent"):
            score += 0.3
        
        # Has budget info
        if lead_data.get("budget"):
            score += 0.2
        
        return min(1.0, score)
    
    def _parse_datetime_from_text(self, text: str) -> Optional[datetime]:
        """Parse datetime from natural language"""
        # Simplified datetime parsing - in production use more sophisticated library
        base_time = datetime.now()
        
        if "tomorrow" in text.lower():
            base_time += timedelta(days=1)
        elif "next week" in text.lower():
            base_time += timedelta(days=7)
        
        # Look for time mentions
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', text.lower())
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            
            if time_match.group(3) == 'pm' and hour != 12:
                hour += 12
            elif time_match.group(3) == 'am' and hour == 12:
                hour = 0
            
            base_time = base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return base_time
    
    # API Methods
    
    def newlead(self, raw: str) -> Lead:
        """Parse and enrich new lead information"""
        request_id = str(uuid.uuid4())
        
        initial_state = DealflowState(
            raw_text=raw,
            request_id=request_id,
            parsed_lead=None,
            enriched_lead=None,
            proposal_content=None,
            schedule_info=None,
            status_info=None,
            error=None
        )
        
        result = self.graph.invoke(initial_state)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        enriched = result.get("enriched_lead", {})
        return Lead(**enriched)
    
    def proposal_copy(self, lead: Dict[str, Any]) -> ProposalCopy:
        """Generate proposal content for lead"""
        request_id = str(uuid.uuid4())
        
        initial_state = DealflowState(
            raw_text="",
            request_id=request_id,
            parsed_lead=lead,
            enriched_lead=None,
            proposal_content=None,
            schedule_info=None,
            status_info=None,
            error=None
        )
        
        result = self._generate_proposal(initial_state)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        proposal = result.get("proposal_content", {})
        return ProposalCopy(**proposal)
    
    def nextstep_parse(self, text: str) -> NextStepSchedule:
        """Parse next step scheduling information"""
        request_id = str(uuid.uuid4())
        
        initial_state = DealflowState(
            raw_text=text,
            request_id=request_id,
            parsed_lead=None,
            enriched_lead=None,
            proposal_content=None,
            schedule_info=None,
            status_info=None,
            error=None
        )
        
        result = self._parse_schedule(initial_state)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        schedule = result.get("schedule_info", {})
        return NextStepSchedule(**schedule)
    
    def status_classify(self, label: str, reason_text: Optional[str] = None) -> StatusClassification:
        """Classify deal status and reason"""
        request_id = str(uuid.uuid4())
        
        raw_text = f"{label}"
        if reason_text:
            raw_text += f" - {reason_text}"
        
        initial_state = DealflowState(
            raw_text=raw_text,
            request_id=request_id,
            parsed_lead=None,
            enriched_lead=None,
            proposal_content=None,
            schedule_info=None,
            status_info=None,
            error=None
        )
        
        result = self._classify_status(initial_state)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        status = result.get("status_info", {})
        return StatusClassification(**status)

# Global agent instance
dealflow_agent = DealflowAgent()
