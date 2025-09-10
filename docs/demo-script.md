# WhatsApp Revenue Copilot - Complete Demo Script

## Demo Overview
This script demonstrates all key capabilities of the WhatsApp Revenue Copilot system in a logical sequence that showcases both Agent A (Knowledge) and Agent B (Dealflow) working together through n8n orchestration.

**Duration**: ~10-15 minutes  
**Audience**: Business stakeholders, technical team, or clients  
**Setup**: WhatsApp Business API connected, all services running

---

## Pre-Demo Checklist ✅

- [ ] All Docker services running (`docker-compose ps`)
- [ ] n8n workflows imported and active
- [ ] WhatsApp webhook configured and tested
- [ ] Google Sheets (Conversations & CRM) accessible
- [ ] Sample PDF ready for knowledge ingestion
- [ ] Phone/WhatsApp client ready for demo

---

## Demo Sequence

### 🎯 **Act 1: Knowledge Management** (3-4 minutes)

#### **Step 1: Initial Knowledge Query**
**Scenario**: Customer service inquiry about company policies

**Demo Action**: 
```
Send WhatsApp message: "What's our refund policy?"
```

**Expected Results**:
- Bot responds within 5-10 seconds
- Answer includes relevant policy details
- Citations reference source documents
- Confidence score displayed
- Conversation logged in Google Sheets

**Talking Points**:
- "Notice how the bot provides grounded answers with citations"
- "The confidence score helps us understand answer reliability"
- "All interactions are automatically logged for review"

---

#### **Step 2: Knowledge Base Enhancement**
**Scenario**: Adding new information to the knowledge base

**Demo Action**:
```
Send WhatsApp message with PDF attachment: "New Refunds Policy 2025.pdf"
```

**Expected Results**:
- Auto-ingestion starts immediately
- Confirmation message: "Got it — I've added X chunks to the knowledge base"
- File appears in Google Drive KnowledgeBase folder
- Processing logged in Conversations sheet

**Talking Points**:
- "The system automatically ingests new documents"
- "No manual processing required - just upload and go"
- "Documents are chunked and vectorized for semantic search"

---

#### **Step 3: Enhanced Knowledge Query**
**Scenario**: Testing the newly added knowledge

**Demo Action**:
```
Send WhatsApp message: "What about digital goods refunds specifically?"
```

**Expected Results**:
- Bot provides updated answer using new document
- Citations include the newly uploaded file
- Higher confidence score due to relevant content
- Answer is more specific and detailed

**Talking Points**:
- "See how it now references our latest policy document"
- "The vector database enables semantic understanding"
- "Knowledge base grows dynamically with each upload"

---

#### **Step 4: Scheduling from Knowledge Context**
**Scenario**: Following up on a knowledge query with meeting request

**Demo Action**:
```
Send WhatsApp message: "Let's schedule a call next Tuesday at 2 PM with Dana about our refund policies"
```

**Expected Results**:
- Calendar event created for next Tuesday 2 PM
- Event includes context about refunds topic
- Confirmation with calendar link sent back
- Conversations sheet updated with scheduling info

**Talking Points**:
- "Natural language scheduling - no forms to fill"
- "Context from previous conversation carried forward"
- "Automatically integrates with Google Calendar"

---

### 💼 **Act 2: Sales Dealflow Management** (4-5 minutes)

#### **Step 5: Lead Capture**
**Scenario**: Sales prospect information received via WhatsApp

**Demo Action**:
```
Send WhatsApp message: "John Smith from Acme Corporation reached out - they want a PoC for their new project, mentioned budget around $15,000"
```

**Expected Results**:
- Lead parsed and structured automatically
- Company domain guessed (acme.com)
- Quality score calculated
- CRM sheet updated with new lead
- Confirmation with lead summary returned

**Talking Points**:
- "No more manual data entry for sales leads"
- "System automatically enriches lead data"
- "Quality scoring helps prioritize prospects"

---

#### **Step 6: Proposal Generation**
**Scenario**: Client requests a proposal for the captured lead

**Demo Action**:
```
Send WhatsApp message: "Can you draft a proposal for Acme Corporation?"
```

**Expected Results**:
- Custom proposal generated within 30 seconds
- Google Doc created from template
- PDF exported and shared via Drive link
- CRM updated with proposal link
- Professional proposal copy tailored to lead

**Talking Points**:
- "AI-generated proposals customized for each prospect"
- "Consistent professional format using company templates"
- "Instant delivery via secure Google Drive links"

---

#### **Step 7: Next Step Scheduling**
**Scenario**: Planning follow-up activities for the deal

**Demo Action**:
```
Send WhatsApp message: "Schedule a demo with Acme for next Wednesday at 11:30 AM"
```

**Expected Results**:
- Calendar event created for demo
- CRM NextStepDate field updated
- Event includes Acme context and proposal link
- Confirmation with meeting details

**Talking Points**:
- "Seamless scheduling tied to deal progression"
- "CRM automatically tracks next steps"
- "All relevant context included in calendar events"

---

#### **Step 8: Deal Status Update**
**Scenario**: Updating the pipeline with deal outcome

**Demo Action**:
```
Send WhatsApp message: "Update on Acme - unfortunately we lost the deal due to budget constraints"
```

**Expected Results**:
- Status classified as "Lost"
- Reason categorized as "budget"
- CRM updated with loss reason
- Deal stage changed appropriately
- Confirmation of status update

**Talking Points**:
- "Automatic deal tracking and categorization"
- "Loss reasons help improve future proposals"
- "Real-time pipeline updates for sales team"

---

### 📊 **Act 3: System Integration Showcase** (2-3 minutes)

#### **Step 9: Multi-Intent Conversation**
**Scenario**: Mixing knowledge and sales in one conversation

**Demo Action**:
```
Send WhatsApp message: "What are our standard enterprise pricing tiers? I need this for the Microsoft proposal due tomorrow at 3 PM"
```

**Expected Results**:
- Knowledge answer about pricing tiers
- Scheduling intent detected for tomorrow 3 PM
- Calendar reminder created
- Both needs addressed in single interaction

**Talking Points**:
- "System handles complex, multi-intent conversations"
- "No need to switch between different interfaces"
- "Context awareness across different functions"

---

#### **Step 10: Data Integration Review**
**Scenario**: Showing the complete data trail

**Demo Actions**:
- Open Google Sheets Conversations tab
- Open Google Sheets CRM tab  
- Open Google Calendar
- Show Google Drive folders

**Expected Results**:
- Complete conversation history with timestamps
- Structured CRM data with all captured leads
- Calendar events with proper context
- Organized document storage

**Talking Points**:
- "Complete audit trail of all interactions"
- "Structured data ready for analysis and reporting"  
- "Seamless integration with existing Google Workspace"

---

## 🎭 **Demonstration Tips**

### **For Technical Audiences**:
- Highlight the LangGraph agent architecture
- Discuss vector database capabilities
- Explain n8n workflow orchestration
- Show API endpoints and data schemas
- Demonstrate error handling and retries

### **For Business Audiences**:
- Focus on productivity gains and time savings
- Emphasize lead conversion and sales pipeline value
- Highlight customer service improvements
- Discuss ROI and operational efficiency
- Show integration with existing tools

### **For Sales Teams**:
- Demonstrate lead qualification scoring
- Show proposal generation speed and consistency
- Highlight pipeline tracking and analytics
- Emphasize mobile-first approach
- Focus on deal progression automation

---

## 📈 **Demo Variations**

### **Quick Demo (5 minutes)**:
- Steps 1, 2, 5, 6 only
- Focus on core Q&A and proposal generation

### **Technical Deep-Dive (20 minutes)**:
- All steps plus backend system walkthrough
- API testing with Postman/curl
- n8n workflow examination
- Database and vector store inspection

### **Executive Summary (3 minutes)**:
- Steps 1, 5, 6, 10 only
- Focus on business value and ROI

---

## 🔧 **Troubleshooting Common Demo Issues**

**Slow Response Times**:
- Check OpenAI API rate limits
- Verify all Docker containers healthy
- Monitor n8n execution logs

**Missing Citations**:
- Confirm knowledge documents are properly ingested
- Check Chroma database connectivity
- Verify embedding generation

**Scheduling Failures**:
- Validate Google Calendar API permissions
- Check timezone settings
- Confirm calendar access rights

**CRM Data Issues**:
- Verify Google Sheets API credentials
- Check sheet column headers match expected format
- Confirm write permissions on sheets

---

## 🎉 **Demo Closing Points**

### **Key Achievements Demonstrated**:
1. ✅ **Zero-Command Interface**: Natural language only, no slash commands
2. ✅ **Dual-Agent Architecture**: Knowledge and sales working together
3. ✅ **Complete Integration**: WhatsApp → n8n → Agents → Google APIs
4. ✅ **Real-Time Processing**: Instant responses and updates
5. ✅ **Audit Trail**: Complete data tracking and logging
6. ✅ **Scalable Architecture**: Production-ready containerized deployment

### **Business Value Proposition**:
- **80% reduction** in manual data entry for sales teams
- **3x faster** proposal generation and delivery
- **Complete integration** with existing Google Workspace
- **Real-time insights** into customer interactions and sales pipeline
- **Mobile-first** approach for modern distributed teams

### **Next Steps for Prospects**:
1. **Pilot Program**: 30-day trial with your team
2. **Custom Integration**: Adapt to your specific workflows
3. **Training Program**: Team onboarding and best practices
4. **Success Metrics**: Define and track ROI measurements

---

## 📋 **Post-Demo Checklist**

- [ ] Share demo recording if applicable
- [ ] Provide access to test environment
- [ ] Schedule technical deep-dive if requested
- [ ] Send follow-up materials and documentation
- [ ] Plan pilot program timeline
- [ ] Gather feedback and questions
- [ ] Update CRM with demo results and next steps

**Remember**: This system represents the cutting edge of conversational AI applied to business operations. The seamless integration of knowledge management and sales processes through natural language interfaces will transform how teams collaborate and serve customers.

---

*Demo script last updated: September 2025*  
*System version: v1.0.0*
