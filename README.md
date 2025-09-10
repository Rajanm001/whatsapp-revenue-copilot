# WhatsApp Revenue Copilot

*Built by Rajan*

A powerful WhatsApp-based business copilot that revolutionizes customer support and sales operations. This system intelligently combines knowledge management and sales pipeline automation using AI agents and workflow orchestration.

## 🚀 What This System Does

Transform your WhatsApp into a powerful business tool that:
- **Answers customer questions** instantly using your company documents
- **Captures leads** automatically from conversations  
- **Generates proposals** with AI-powered copywriting
- **Schedules meetings** from natural language requests
- **Tracks sales pipeline** in real-time

Perfect for businesses wanting to automate customer support and sales without losing the personal touch.

## 🚀 Quick Start

### ⚡ One-Command Launch (Recommended)

**Windows (PowerShell):**
```powershell
.\quick-start.ps1
```

**Linux/Mac:**
```bash
chmod +x quick-start.sh && ./quick-start.sh
```

The quick-start scripts automatically:
- ✅ Check prerequisites (Docker, Docker Compose)
- ✅ Create environment configuration from template
- ✅ Set up data directories
- ✅ Build and launch all services
- ✅ Validate service health
- ✅ Display service URLs and next steps

### Manual Setup

### Prerequisites

1. **OpenAI API Key**: For LLM capabilities
2. **Google Cloud Project**: With Drive, Sheets, Calendar APIs enabled
3. **WhatsApp Business API**: Access token and phone number ID
4. **Docker & Docker Compose**: For containerized deployment

### 1. Clone and Setup

```bash
git clone <repository>
cd whatsapp-revenue-copilot
```

### 2. Environment Configuration

```bash
cp infra/env.sample .env
# Edit .env with your actual credentials
```

**Required Environment Variables:**
```env
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
CONVERSATIONS_SHEET_ID=1abc...
CRM_SHEET_ID=1def...
WHATSAPP_ACCESS_TOKEN=EAAx...
WHATSAPP_PHONE_NUMBER_ID=123...
```

### 3. Google Cloud Setup

1. Create a new Google Cloud Project
2. Enable APIs: Drive, Sheets, Calendar
3. Create a Service Account with appropriate scopes:
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/spreadsheets`  
   - `https://www.googleapis.com/auth/calendar`
4. Download service account key JSON
5. Create Google Sheets:
   - **Conversations Sheet**: Timestamp, User, Intent, Input, Output, Confidence, Citations, Error
   - **CRM Sheet**: Timestamp, LeadId, Name, Company, Intent, Budget, Stage, Owner, NextStepDate, Links, Notes

### 4. WhatsApp Business Setup

1. Get WhatsApp Business API access
2. Configure webhook URL: `https://your-domain.com/webhook/whatsapp`
3. Set verify token in environment variables

### 5. Deploy with Docker

```bash
# Build and start all services
cd infra
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

Services will be available at:
- **n8n**: http://localhost:5678 (admin/admin123)
- **Agent A**: http://localhost:8001
- **Agent B**: http://localhost:8002
- **Chroma**: http://localhost:8000
- **Intent Classifier**: http://localhost:8000

### 6. Import n8n Workflows

1. Open n8n at http://localhost:5678
2. Import workflows from `n8n/workflows/`:
   - `whatsapp_router.json` - Main message routing
   - `drive_watch.json` - Auto-ingestion from Drive
   - `nightly_reindex.json` - Maintenance tasks

### 7. Test the System

Send test messages to your WhatsApp number:

```
"What's our refund policy?" 
→ Knowledge Q&A

"John from Acme wants a PoC, budget 10k"
→ Lead capture

"Draft a proposal for Acme"
→ Proposal generation

"Schedule demo next Wed at 11am"
→ Calendar booking

[Send a PDF file]
→ Auto ingestion
```

## 📋 System Workflows

### Knowledge Q&A Flow
1. User sends question → n8n webhook
2. Intent classified as `knowledge_qa`
3. Agent A retrieves relevant docs from Chroma
4. LLM generates grounded answer with citations
5. Response sent via WhatsApp
6. Conversation logged to Sheets

### Lead Capture Flow
1. User mentions prospect info → n8n webhook
2. Intent classified as `lead_capture` 
3. Agent B parses contact/company/budget
4. Data enriched (domain guess, quality score)
5. CRM Sheet updated with new lead
6. Confirmation sent to user

### Proposal Generation Flow  
1. User requests proposal → n8n webhook
2. Intent classified as `proposal_request`
3. Agent B generates customized proposal
4. Google Doc created from template
5. PDF exported and shared via Drive link
6. CRM updated with proposal link

### Document Ingestion Flow
1. File uploaded to Drive folder (watch trigger)
2. Agent A chunks and embeds content
3. Vectors stored in Chroma database
4. Admin notified of successful ingestion
5. File searchable in knowledge base

## 🔧 API Reference

### Agent A Endpoints

**POST /agentA/ingest**
```json
{
  "driveFileId": "1abc123..."
}
```

**POST /agentA/ask** 
```json
{
  "userId": "user123",
  "text": "What's our refund policy?"
}
```

**POST /agentA/followup-parse**
```json
{
  "text": "Schedule call next Tuesday at 10am"
}
```

### Agent B Endpoints

**POST /agentB/newlead**
```json
{
  "raw": "John from Acme wants PoC, budget 10k"
}
```

**POST /agentB/proposal-copy**
```json
{
  "lead": {
    "name": "John Smith",
    "company": "Acme Corp",
    "intent": "PoC request"
  }
}
```

**POST /agentB/nextstep-parse**
```json
{
  "text": "Schedule demo next Wednesday at 11am"
}
```

**POST /agentB/status-classify**
```json
{
  "label": "Lost",
  "reasonText": "budget cut"
}
```

## 🧪 Testing

Run unit tests:
```bash
# Agent A tests
cd agents/agentA_knowledge
python -m pytest tests/ -v

# Agent B tests  
cd agents/agentB_dealflow
python -m pytest tests/ -v
```

Test API endpoints:
```bash
# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health

# Test knowledge Q&A
curl -X POST http://localhost:8001/agentA/ask \
  -H "Content-Type: application/json" \
  -d '{"userId": "test", "text": "What is our refund policy?"}'
```

## 📊 Monitoring & Observability

### Logs
- **Docker Logs**: `docker-compose logs -f [service]`
- **Application Logs**: Structured JSON logging with request IDs
- **n8n Execution Logs**: Available in n8n UI

### Health Checks
All services include health check endpoints and Docker health checks.

### Metrics (Optional Enhancement)
- Message processing latency
- Q&A confidence scores  
- Lead conversion rates
- Vector store hit rates

## 🔒 Security Considerations

1. **API Keys**: Never commit keys to repo
2. **Google Scopes**: Use least-privilege access
3. **Input Sanitization**: Basic validation in place
4. **Network Security**: Services isolated in Docker network
5. **Authentication**: n8n basic auth enabled

## 🛠️ Development

### Local Development Setup
```bash
# Install Python dependencies
cd agents/agentA_knowledge
pip install -r requirements.txt

# Run agents locally
python app.py  # Agent A on :8001
cd ../agentB_dealflow  
python app.py  # Agent B on :8002
```

### Adding New Intents
1. Update `shared/intent_classifier.py` with new intent
2. Add routing logic in n8n workflow
3. Implement handler in appropriate agent
4. Add tests and documentation

### Extending Agents
- **Agent A**: Add new document types, improve citations
- **Agent B**: Add lead scoring, custom proposal templates
- **Both**: Add self-reflection, error handling, retries

## 📈 Scaling Considerations

### Performance
- **Horizontal Scaling**: Multiple agent instances behind load balancer
- **Caching**: Redis for conversation context
- **Queue**: Celery for background processing
- **Database**: PostgreSQL for persistence

### Reliability
- **Circuit Breakers**: Prevent cascade failures
- **Retries**: Exponential backoff for external APIs
- **Monitoring**: Prometheus + Grafana
- **Alerting**: PagerDuty integration

## 🏆 Demo Script

Follow this script to demonstrate all capabilities:

1. **Knowledge Q&A**: "What's our refund policy?"
2. **File Upload**: Send a PDF → auto-ingestion
3. **Enhanced Q&A**: "What about digital goods refunds?" 
4. **Scheduling**: "Schedule call Tuesday 10am with Dana about refunds"
5. **Lead Capture**: "John from Acme wants PoC, budget 10k"
6. **Proposal**: "Draft proposal for Acme"
7. **Next Step**: "Schedule demo next Wed at 11am"
8. **Status Update**: "We lost Acme - budget cut"
9. **Show Sheets**: Conversations + CRM data
10. **Show Calendar**: Created events

Expected results: All interactions logged, CRM updated, proposals generated, meetings scheduled.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Agent fails to start**:
- Check OpenAI API key is valid
- Verify Chroma is accessible
- Check Docker network connectivity

**n8n workflows fail**:  
- Verify Google API credentials
- Check WhatsApp webhook configuration
- Ensure Sheet IDs are correct

**Knowledge retrieval poor**:
- Check document ingestion logs
- Verify Chroma embeddings stored
- Adjust chunk size/overlap parameters

**Intent classification incorrect**:
- Review classifier prompt
- Add more training examples  
- Adjust confidence thresholds

### Getting Help

1. Check Docker logs: `docker-compose logs -f`
2. Test individual services: `curl http://localhost:800X/health`
3. Review n8n execution logs
4. Open GitHub issue with logs and reproduction steps

## 🔄 Updates & Maintenance

### Regular Tasks
- **Weekly**: Review conversation logs, adjust prompts
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Evaluate new LLM models, optimize costs

### Backup Strategy
- **Code**: Git repository with tags
- **Data**: Chroma database backups
- **Configurations**: n8n workflow exports
- **Secrets**: Secure key management

---

**Built with ❤️ by Rajan using LangGraph, n8n, and FastAPI**

## 📈 Project Stats
- **Development Time**: 3 weeks
- **Technologies**: Python, LangGraph, n8n, Docker, FastAPI
- **Integrations**: WhatsApp, Google Drive, Sheets, Calendar
- **Status**: Production Ready ✅
