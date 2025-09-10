# Production Deployment Guide

## Prerequisites

### System Requirements
- **Docker**: Version 20.10+ with Docker Compose
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 50GB+ available space
- **CPU**: 4+ cores recommended
- **Network**: Stable internet with webhook accessibility

### Required Accounts & APIs
- **OpenAI Account**: API key with sufficient credits
- **Google Cloud Project**: With enabled APIs (Drive, Sheets, Calendar)
- **WhatsApp Business API**: Access token and phone number
- **Domain/Server**: For webhook endpoints (HTTPS required)

## Step-by-Step Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. Project Deployment

```bash
# Clone repository
git clone <your-repo-url>
cd whatsapp-revenue-copilot

# Copy environment template
cp infra/env.sample .env

# Edit environment variables
nano .env
```

### 3. Google Cloud Configuration

#### Create Service Account
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
source ~/.bashrc
gcloud init

# Create service account
gcloud iam service-accounts create whatsapp-copilot \
    --display-name="WhatsApp Copilot Service"

# Generate key file
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=whatsapp-copilot@PROJECT_ID.iam.gserviceaccount.com

# Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:whatsapp-copilot@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/drive.file"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:whatsapp-copilot@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spreadsheets.editor"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:whatsapp-copilot@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/calendar.editor"
```

#### Create Google Sheets
```bash
# Create Conversations Sheet with headers:
# Timestamp | User | Intent | Input | Output | Confidence | Citations | Error

# Create CRM Sheet with headers:
# Timestamp | LeadId | Name | Company | Intent | Budget | Stage | Owner | NextStepDate | Links | Notes

# Note the Sheet IDs from URLs and add to .env
```

### 4. WhatsApp Business API Setup

```bash
# In Facebook Developers Console:
# 1. Create WhatsApp Business App
# 2. Configure webhook URL: https://yourdomain.com/webhook/whatsapp-inbound
# 3. Set verify token in .env
# 4. Get access token and phone number ID
# 5. Add webhook fields: messages, message_deliveries, message_reads
```

### 5. SSL Certificate Setup

```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/whatsapp-copilot

# Add configuration:
server {
    listen 80;
    server_name yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site and get certificate
sudo ln -s /etc/nginx/sites-available/whatsapp-copilot /etc/nginx/sites-enabled/
sudo certbot --nginx -d yourdomain.com
```

### 6. Deploy Application

```bash
# Build and start services
docker-compose -f infra/docker-compose.yml up --build -d

# Verify all services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

### 7. Import n8n Workflows

```bash
# Access n8n at https://yourdomain.com
# Login with credentials from .env
# Import workflows from n8n/workflows/
# Activate all workflows
# Test webhook endpoint
```

## Production Optimizations

### 1. Performance Tuning

```yaml
# docker-compose.prod.yml additions
version: '3.8'
services:
  agenta:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    environment:
      - WORKERS=4
      - MAX_REQUESTS=1000

  agentb:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  chroma:
    volumes:
      - /data/chroma:/chroma/chroma  # Use dedicated storage
```

### 2. Monitoring Setup

```bash
# Add Prometheus monitoring
cat >> docker-compose.yml << 'EOF'
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
EOF
```

### 3. Backup Strategy

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/whatsapp-copilot"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Chroma database
docker run --rm -v whatsapp-copilot_chroma_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/chroma_$DATE.tar.gz /data

# Backup n8n data
docker run --rm -v whatsapp-copilot_n8n_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/n8n_$DATE.tar.gz /data

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh

# Add to crontab for daily backups
echo "0 3 * * * /path/to/backup.sh" | crontab -
```

### 4. Security Hardening

```bash
# Firewall setup
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Docker security
echo '{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "userland-proxy": false,
  "experimental": false,
  "icc": false
}' | sudo tee /etc/docker/daemon.json

sudo systemctl restart docker
```

## Health Checks & Monitoring

### 1. Service Health Monitoring

```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash

# Check all services
services=("agenta:8001" "agentb:8002" "chroma:8000" "n8n:5678")

for service in "${services[@]}"; do
    IFS=':' read -ra ADDR <<< "$service"
    if curl -f http://localhost:${ADDR[1]}/health > /dev/null 2>&1; then
        echo "✅ ${ADDR[0]} is healthy"
    else
        echo "❌ ${ADDR[0]} is down"
        # Send alert (integrate with your monitoring system)
    fi
done
EOF

chmod +x health_check.sh

# Run every 5 minutes
echo "*/5 * * * * /path/to/health_check.sh" | crontab -
```

### 2. Log Management

```bash
# Setup log rotation
cat > /etc/logrotate.d/whatsapp-copilot << 'EOF'
/var/log/whatsapp-copilot/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
```

## Scaling Considerations

### 1. Horizontal Scaling

```yaml
# Load balancer configuration
version: '3.8'
services:
  nginx-lb:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - agenta1
      - agenta2
      - agentb1
      - agentb2

  agenta1:
    build: ./agents/agentA_knowledge
    environment:
      - INSTANCE_ID=1

  agenta2:
    build: ./agents/agentA_knowledge
    environment:
      - INSTANCE_ID=2
```

### 2. Database Scaling

```bash
# For larger deployments, consider:
# - Chroma cluster setup
# - PostgreSQL for metadata
# - Redis for caching
# - Elasticsearch for logs
```

## Maintenance Procedures

### 1. Regular Updates

```bash
# Weekly update routine
docker-compose pull
docker-compose up -d --force-recreate
docker system prune -f
```

### 2. Performance Monitoring

```bash
# Monitor resource usage
docker stats
df -h
free -h
iostat -x 1 10
```

### 3. Troubleshooting

```bash
# Common issues and solutions

# Agent not responding
docker-compose restart agenta
docker-compose logs agenta

# n8n workflow failures
# Check n8n execution logs in UI
# Verify API credentials
# Test webhook endpoints

# Vector search poor results
# Check Chroma database size
# Verify embedding model consistency
# Re-index knowledge base if needed
```

## Security Checklist

- [ ] SSL certificates configured and auto-renewing
- [ ] Environment variables secured and not in code
- [ ] Google service account with minimal permissions
- [ ] Firewall rules properly configured
- [ ] Regular security updates scheduled
- [ ] API rate limiting implemented
- [ ] Input validation and sanitization in place
- [ ] Backup and disaster recovery tested

## Support & Maintenance

### Emergency Contacts
- **Technical Lead**: your-email@company.com
- **Infrastructure**: ops-team@company.com
- **Business Owner**: business-lead@company.com

### Documentation Links
- **System Architecture**: /docs/architecture.md
- **API Reference**: /docs/api-reference.md
- **Troubleshooting Guide**: /docs/troubleshooting.md
- **User Manual**: /docs/user-guide.md

### SLA Commitments
- **Uptime**: 99.5% (excluding planned maintenance)
- **Response Time**: <2 seconds for standard queries
- **Support Response**: <4 hours for critical issues

---

**Deployment completed successfully! 🎉**

Your WhatsApp Revenue Copilot is now production-ready and serving customers.
