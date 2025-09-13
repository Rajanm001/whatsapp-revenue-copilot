# 📥 n8n Workflow Import Guide

## 🎯 Quick Import Steps

### 1. Access n8n Dashboard
- Start system: `docker-compose up -d`
- Open: http://localhost:5678
- Login: admin / admin123

### 2. Import Workflows

**Method 1: Copy-Paste (Recommended)**

1. **WhatsApp Router Workflow**:
   - Go to n8n dashboard
   - Click "New workflow"
   - Click the "..." menu → "Import from URL/File" → "Paste JSON"
   - Copy entire content from `n8n/workflows/whatsapp_router.json`
   - Paste and click "Import"
   - Save as "WhatsApp Revenue Copilot - Main Router"

2. **Drive Watch Workflow**:
   - Click "New workflow" again
   - Copy content from `n8n/workflows/drive_watch.json`
   - Import and save as "Google Drive File Watcher"

3. **Nightly Reindex Workflow**:
   - Copy content from `n8n/workflows/nightly_reindex.json`
   - Import and save as "Nightly Knowledge Base Reindex"

**Method 2: File Upload**

1. Click "Import from URL/File" → "Select file to upload"
2. Upload each JSON file from `n8n/workflows/`
3. Save with appropriate names

### 3. Configure Credentials

**Google APIs**:
1. Go to "Settings" → "Credentials"
2. Click "Add credential" → "Google"
3. Choose "OAuth2" method
4. Enter your Google Client ID and Secret
5. Authorize access

**WhatsApp Business API**:
1. Add credential type "HTTP Header Auth"
2. Name: "WhatsApp API"
3. Header: "Authorization"
4. Value: "Bearer YOUR_WHATSAPP_TOKEN"

### 4. Update Environment Variables

Edit nodes to use environment variables:
- `{{$env.CONVERSATIONS_SHEET_ID}}`
- `{{$env.CRM_SHEET_ID}}`
- `{{$env.WHATSAPP_ACCESS_TOKEN}}`
- `{{$env.WHATSAPP_PHONE_NUMBER_ID}}`

### 5. Test Workflows

1. **Test WhatsApp Router**:
   - Click "Execute" on webhook node
   - Use test payload:
   ```json
   {
     "body": {
       "from": "1234567890",
       "text": "What's our refund policy?",
       "type": "text"
     }
   }
   ```

2. **Test Drive Watch**:
   - Upload a test file to your Google Drive folder
   - Check if auto-ingestion triggers

3. **Test Nightly Reindex**:
   - Manually trigger the cron workflow
   - Verify maintenance logging

## 🚨 Troubleshooting

### Common Import Issues

**Error: "propertyValues[itemName] is not iterable"**
- ✅ Fixed in current workflow versions
- This was caused by incorrect node parameter structure
- New workflows use proper n8n format

**Workflow doesn't execute**
- Check all credentials are configured
- Verify environment variables are set
- Test individual nodes first

**Node connection errors**
- Ensure all required services are running
- Check Docker network connectivity
- Verify endpoint URLs (agenta:8001, agentb:8002, etc.)

### Validation Checklist

- [ ] All 3 workflows imported successfully
- [ ] Google credentials configured and authorized
- [ ] WhatsApp credentials added
- [ ] Environment variables updated in .env
- [ ] Test execution works for main router
- [ ] Docker services are running
- [ ] Agent APIs respond at localhost:8001, localhost:8002

## ✅ Success Indicators

When properly imported, you should see:
- ✅ 3 active workflows in n8n dashboard
- ✅ Green status indicators on all nodes
- ✅ Successful test executions
- ✅ Webhook URL available for WhatsApp
- ✅ File uploads trigger auto-ingestion
- ✅ Messages route to correct agents

## 🔗 Webhook URL

After importing WhatsApp router workflow:
- Webhook URL: `http://YOUR_DOMAIN:5678/webhook/whatsapp-inbound`
- Use this URL in WhatsApp Business API webhook configuration
- For local testing: `http://localhost:5678/webhook/whatsapp-inbound`

**Your n8n workflows are now ready for production! 🚀**
