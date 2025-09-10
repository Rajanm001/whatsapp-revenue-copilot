"""
WhatsApp Knowledge Agent - By Rajan
This agent handles all knowledge-related queries, document processing, and scheduling.
Built to make customer support smarter and more efficient.
"""

from typing import Dict, Any, List, Optional, TypedDict
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import chromadb
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import uuid
from datetime import datetime, timedelta
import re
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Citation(BaseModel):
    """Citation for knowledge answers"""
    title: str = Field(description="Document title")
    drive_file_id: str = Field(description="Google Drive file ID")
    page_ranges: Optional[List[str]] = Field(default=None, description="Page numbers or sections")
    snippet: str = Field(description="Relevant text snippet")

class KnowledgeAnswer(BaseModel):
    """Knowledge agent response"""
    answer: str = Field(description="Generated answer")
    citations: List[Citation] = Field(description="Supporting citations")
    confidence: float = Field(description="Confidence score 0-1")
    request_id: str = Field(description="Request tracking ID")

class FollowUpSchedule(BaseModel):
    """Parsed scheduling information"""
    title: str = Field(description="Meeting title")
    start_iso: str = Field(description="Start time in ISO format")
    end_iso: Optional[str] = Field(description="End time in ISO format")
    attendees: Optional[List[str]] = Field(default=None, description="Attendee names/emails")
    request_id: str = Field(description="Request tracking ID")

class IngestionResult(BaseModel):
    """Document ingestion result"""
    chunks: int = Field(description="Number of chunks created")
    tokens: int = Field(description="Approximate token count")
    request_id: str = Field(description="Request tracking ID")

class KnowledgeState(TypedDict):
    """State for knowledge agent graph"""
    user_id: str
    query: str
    drive_file_id: Optional[str]
    request_id: str
    chunks: List[Document]
    retrieved_docs: List[Document]
    answer: str
    citations: List[Citation]
    confidence: float
    follow_up_info: Optional[Dict[str, Any]]
    error: Optional[str]

class KnowledgeAgent:
    """LangGraph agent for knowledge management and Q&A"""
    
    def __init__(self, chroma_path: str = "./data/chroma"):
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=1000
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(KnowledgeState)
        
        # Add nodes
        workflow.add_node("ingest_node", self._ingest_document)
        workflow.add_node("retrieve_node", self._retrieve_documents) 
        workflow.add_node("answer_node", self._generate_answer)
        workflow.add_node("reflect_node", self._self_reflect)
        workflow.add_node("schedule_parse_node", self._parse_scheduling)
        
        # Add edges
        workflow.add_conditional_edges(
            "ingest_node",
            self._route_after_ingest,
            {"end": END, "continue": "retrieve_node"}
        )
        
        workflow.add_edge("retrieve_node", "answer_node")
        workflow.add_edge("answer_node", "reflect_node")
        workflow.add_conditional_edges(
            "reflect_node",
            self._route_after_reflection,
            {"schedule": "schedule_parse_node", "end": END}
        )
        workflow.add_edge("schedule_parse_node", END)
        
        # Set entry point
        workflow.set_entry_point("ingest_node")
        
        return workflow.compile()
    
    def _ingest_document(self, state: KnowledgeState) -> KnowledgeState:
        """Ingest and embed document from Drive"""
        try:
            if not state.get("drive_file_id"):
                return {**state, "error": "No drive file ID provided"}
            
            # In a real implementation, you'd download from Google Drive
            # For now, we'll simulate with placeholder content
            logger.info(f"Ingesting document {state['drive_file_id']}")
            
            # Simulate document content (in real implementation, fetch from Drive)
            mock_content = f"""
            Sample document content for file {state['drive_file_id']}.
            This would contain the actual document text retrieved from Google Drive.
            Company refund policy: All purchases can be refunded within 30 days.
            Digital goods have a 7-day refund window.
            For enterprise clients, custom refund terms apply.
            """
            
            # Split into chunks
            docs = [Document(
                page_content=mock_content,
                metadata={
                    "source": state["drive_file_id"],
                    "title": f"Document {state['drive_file_id']}",
                    "ingestion_time": datetime.now().isoformat()
                }
            )]
            
            chunks = self.text_splitter.split_documents(docs)
            
            # Embed and store
            texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embeddings.embed_documents(texts)
            
            # Store in Chroma
            chunk_ids = [f"{state['drive_file_id']}_chunk_{i}" for i in range(len(chunks))]
            
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=[chunk.metadata for chunk in chunks],
                ids=chunk_ids
            )
            
            state["chunks"] = chunks
            logger.info(f"Ingested {len(chunks)} chunks from {state['drive_file_id']}")
            
        except Exception as e:
            logger.error(f"Ingestion error: {e}")
            state["error"] = str(e)
        
        return state
    
    def _retrieve_documents(self, state: KnowledgeState) -> KnowledgeState:
        """Retrieve relevant documents for query"""
        try:
            query = state.get("query", "")
            if not query:
                return {**state, "error": "No query provided"}
            
            # Embed query
            query_embedding = self.embeddings.embed_query(query)
            
            # Search Chroma
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to Documents
            retrieved_docs = []
            for i, doc in enumerate(results["documents"][0]):
                retrieved_docs.append(Document(
                    page_content=doc,
                    metadata=results["metadatas"][0][i]
                ))
            
            state["retrieved_docs"] = retrieved_docs
            logger.info(f"Retrieved {len(retrieved_docs)} documents for query: {query}")
            
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            state["error"] = str(e)
        
        return state
    
    def _generate_answer(self, state: KnowledgeState) -> KnowledgeState:
        """Generate grounded answer with citations"""
        try:
            query = state.get("query", "")
            docs = state.get("retrieved_docs", [])
            
            if not docs:
                state["answer"] = "I don't have relevant information to answer that question."
                state["confidence"] = 0.1
                state["citations"] = []
                return state
            
            # Build context from retrieved docs
            context = "\n\n".join([
                f"[{i+1}] {doc.page_content[:500]}..." 
                for i, doc in enumerate(docs)
            ])
            
            # Generate answer
            prompt = f"""Based on the following context, answer the user's question. 
            Be concise and accurate. Cite sources using [1], [2], etc.

Context:
{context}

Question: {query}

Answer with citations:"""
            
            response = self.llm.invoke(prompt)
            answer = response.content
            
            # Create citations
            citations = []
            for i, doc in enumerate(docs):
                citations.append(Citation(
                    title=doc.metadata.get("title", f"Document {i+1}"),
                    drive_file_id=doc.metadata.get("source", "unknown"),
                    snippet=doc.page_content[:200],
                    page_ranges=None
                ))
            
            # Simple confidence scoring based on relevance
            confidence = min(0.9, len([d for d in docs if len(d.page_content) > 100]) * 0.2)
            
            state["answer"] = answer
            state["citations"] = citations
            state["confidence"] = confidence
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            state["error"] = str(e)
        
        return state
    
    def _self_reflect(self, state: KnowledgeState) -> KnowledgeState:
        """Self-reflect on answer quality and detect follow-up scheduling"""
        try:
            answer = state.get("answer", "")
            confidence = state.get("confidence", 0.0)
            query = state.get("query", "")
            
            # Check for scheduling intent in query
            scheduling_keywords = [
                "schedule", "meeting", "call", "appointment", "book", 
                "set up", "arrange", "calendar", "time", "when", "available"
            ]
            
            has_scheduling = any(keyword in query.lower() for keyword in scheduling_keywords)
            
            if has_scheduling:
                # Extract potential scheduling info
                schedule_info = self._extract_time_info(query)
                state["follow_up_info"] = schedule_info
            
            # Quality reflection
            if confidence < 0.6:
                reflection_prompt = f"""
                Review this Q&A for accuracy and completeness:
                
                Question: {query}
                Answer: {answer}
                Confidence: {confidence}
                
                Is the answer accurate and complete? Should we request clarification?
                Respond with brief assessment.
                """
                
                reflection = self.llm.invoke(reflection_prompt)
                logger.info(f"Self-reflection: {reflection.content}")
                
                if confidence < 0.3:
                    state["answer"] += "\n\n(Note: I'm not very confident in this answer. Could you provide more specific details or rephrase your question?)"
            
        except Exception as e:
            logger.error(f"Reflection error: {e}")
        
        return state
    
    def _parse_scheduling(self, state: KnowledgeState) -> KnowledgeState:
        """Parse scheduling information from natural language"""
        try:
            query = state.get("query", "")
            time_info = self._extract_time_info(query)
            
            if time_info:
                # Create structured scheduling result
                start_time = self._parse_datetime(time_info.get("time_str", ""))
                
                if start_time:
                    state["follow_up_info"] = {
                        "title": time_info.get("title", "Follow-up meeting"),
                        "start_iso": start_time.isoformat(),
                        "end_iso": (start_time + timedelta(hours=1)).isoformat(),
                        "attendees": time_info.get("attendees", [])
                    }
            
        except Exception as e:
            logger.error(f"Scheduling parse error: {e}")
        
        return state
    
    def _extract_time_info(self, text: str) -> Dict[str, Any]:
        """Extract scheduling information from text"""
        # Simple regex patterns for time extraction
        patterns = {
            "time": r"\b(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?\b",
            "day": r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today)\b",
            "date": r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            "with": r"\bwith\s+([A-Za-z\s]+?)(?:\s+about|\s+regarding|$)",
            "about": r"\babout\s+([A-Za-z\s]+?)(?:\.|$)"
        }
        
        extracted = {}
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                extracted[key] = matches
        
        return extracted
    
    def _parse_datetime(self, time_str: str) -> Optional[datetime]:
        """Parse natural language time to datetime"""
        # Simple implementation - in production, use more sophisticated parsing
        try:
            # This is a placeholder - implement proper datetime parsing
            base_time = datetime.now() + timedelta(days=1)  # Default to tomorrow
            return base_time.replace(hour=10, minute=0, second=0, microsecond=0)
        except:
            return None
    
    def _route_after_ingest(self, state: KnowledgeState) -> str:
        """Route after document ingestion"""
        if state.get("query"):
            return "continue"
        return "end"
    
    def _route_after_reflection(self, state: KnowledgeState) -> str:
        """Route after self-reflection"""
        if state.get("follow_up_info"):
            return "schedule"
        return "end"
    
    # API Methods
    
    def ingest(self, drive_file_id: str) -> IngestionResult:
        """Ingest a document from Google Drive"""
        request_id = str(uuid.uuid4())
        
        initial_state = KnowledgeState(
            user_id="system",
            query="",
            drive_file_id=drive_file_id,
            request_id=request_id,
            chunks=[],
            retrieved_docs=[],
            answer="",
            citations=[],
            confidence=0.0,
            follow_up_info=None,
            error=None
        )
        
        result = self.graph.invoke(initial_state)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        return IngestionResult(
            chunks=len(result.get("chunks", [])),
            tokens=sum(len(chunk.page_content.split()) for chunk in result.get("chunks", [])),
            request_id=request_id
        )
    
    def ask(self, user_id: str, text: str) -> KnowledgeAnswer:
        """Answer a question with grounded response"""
        request_id = str(uuid.uuid4())
        
        initial_state = KnowledgeState(
            user_id=user_id,
            query=text,
            drive_file_id=None,
            request_id=request_id,
            chunks=[],
            retrieved_docs=[],
            answer="",
            citations=[],
            confidence=0.0,
            follow_up_info=None,
            error=None
        )
        
        result = self.graph.invoke(initial_state)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        return KnowledgeAnswer(
            answer=result["answer"],
            citations=result["citations"],
            confidence=result["confidence"],
            request_id=request_id
        )
    
    def followup_parse(self, text: str) -> FollowUpSchedule:
        """Parse scheduling information from text"""
        request_id = str(uuid.uuid4())
        
        initial_state = KnowledgeState(
            user_id="system",
            query=text,
            drive_file_id=None,
            request_id=request_id,
            chunks=[],
            retrieved_docs=[],
            answer="",
            citations=[],
            confidence=0.0,
            follow_up_info=None,
            error=None
        )
        
        # Run only scheduling parse
        result = self._parse_scheduling(initial_state)
        
        if not result.get("follow_up_info"):
            raise Exception("Could not parse scheduling information")
        
        info = result["follow_up_info"]
        return FollowUpSchedule(
            title=info["title"],
            start_iso=info["start_iso"],
            end_iso=info.get("end_iso"),
            attendees=info.get("attendees"),
            request_id=request_id
        )

# Global agent instance
knowledge_agent = KnowledgeAgent()
