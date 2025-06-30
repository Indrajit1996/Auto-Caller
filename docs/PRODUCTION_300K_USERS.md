# Production Deployment Guide for 300k Users

## Overview
This guide covers deploying the Auto-Caller application to handle 300k users with 24/7 availability.

## Architecture Requirements

### 1. Load Balancing & Scaling
- **Load Balancer**: AWS ALB or Google Cloud Load Balancer
- **Auto-scaling**: Minimum 3-5 backend instances
- **Database**: Managed PostgreSQL (RDS/Aurora or Cloud SQL)
- **Redis**: Managed Redis (ElastiCache or Memorystore)
- **CDN**: CloudFront or Cloud CDN for static assets

### 2. Webhook Infrastructure
For 300k users, you need a **public webhook URL** that Twilio can reach:

```bash
# Set your production domain
WEBHOOK_BASE_URL=https://your-production-domain.com
```

**Options for webhook hosting:**
- **AWS**: API Gateway + Lambda or ECS/Fargate
- **Google Cloud**: Cloud Run or GKE
- **Azure**: App Service or AKS
- **Self-hosted**: Kubernetes with ingress controller

### 3. Database Scaling
```sql
-- Recommended PostgreSQL configuration for 300k users
max_connections = 200
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 16MB
maintenance_work_mem = 256MB
```

### 4. Twilio Account Scaling
- **Upgrade from trial**: Contact Twilio sales for production account
- **Request higher limits**: 
  - Concurrent calls: 1000+
  - API rate limits: 1000+ requests/second
  - Phone numbers: Multiple numbers for load distribution

## Deployment Steps

### 1. Production Environment Setup
```bash
# Update environment variables
WEBHOOK_BASE_URL=https://your-production-domain.com
TWILIO_ACCOUNT_SID=your_production_sid
TWILIO_AUTH_TOKEN=your_production_token
TWILIO_PHONE_NUMBER=your_production_number

# Database
POSTGRES_SERVER=your-production-db-host
POSTGRES_USER=your_production_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=autocaller_prod

# Redis
REDIS_HOST=your-production-redis-host
REDIS_PORT=6379
```

### 2. Kubernetes Deployment (Recommended)
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autocaller-backend
spec:
  replicas: 5  # Start with 5 instances
  selector:
    matchLabels:
      app: autocaller-backend
  template:
    metadata:
      labels:
        app: autocaller-backend
    spec:
      containers:
      - name: backend
        image: your-registry/autocaller-backend:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        env:
        - name: WEBHOOK_BASE_URL
          value: "https://your-production-domain.com"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 3. Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: autocaller-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: autocaller-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 4. Ingress Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autocaller-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-production-domain.com
    secretName: autocaller-tls
  rules:
  - host: your-production-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: autocaller-backend-service
            port:
              number: 80
```

## Monitoring & Observability

### 1. Application Metrics
- **Call success rate**: Target >99%
- **Response time**: Target <2 seconds
- **Error rate**: Target <1%
- **Concurrent calls**: Monitor capacity

### 2. Infrastructure Metrics
- **CPU utilization**: Target <70%
- **Memory usage**: Target <80%
- **Database connections**: Monitor pool usage
- **Redis hit rate**: Target >95%

### 3. Logging
```yaml
# Structured logging for production
logging:
  level: INFO
  format: json
  output: stdout
```

## Security Considerations

### 1. API Security
- **Rate limiting**: Implement per-user limits
- **Authentication**: JWT tokens with short expiry
- **CORS**: Restrict to your frontend domains
- **HTTPS**: Enforce TLS 1.3

### 2. Secrets Management
```bash
# Use Kubernetes secrets or external secret managers
kubectl create secret generic autocaller-secrets \
  --from-literal=twilio-auth-token=your_token \
  --from-literal=postgres-password=your_password \
  --from-literal=secret-key=your_secret_key
```

### 3. Network Security
- **VPC**: Isolate resources in private subnets
- **Security Groups**: Restrict access to necessary ports
- **WAF**: Protect against common attacks

## Performance Optimization

### 1. Database Optimization
```sql
-- Create indexes for common queries
CREATE INDEX idx_calls_user_id ON calls(user_id);
CREATE INDEX idx_calls_created_at ON calls(created_at);
CREATE INDEX idx_users_email ON users(email);

-- Partition large tables
CREATE TABLE calls_partitioned (
  LIKE calls INCLUDING ALL
) PARTITION BY RANGE (created_at);
```

### 2. Caching Strategy
```python
# Redis caching for frequently accessed data
@cache(expire=300)  # 5 minutes
async def get_user_settings(user_id: int):
    # Cache user settings
    pass

@cache(expire=60)   # 1 minute
async def get_call_status(call_sid: str):
    # Cache call status
    pass
```

### 3. Connection Pooling
```python
# Database connection pooling
DATABASE_URL = "postgresql://user:pass@host/db?pool_size=20&max_overflow=30"
```

## Disaster Recovery

### 1. Backup Strategy
- **Database**: Daily automated backups with point-in-time recovery
- **Application**: Container images in multiple registries
- **Configuration**: Version-controlled in Git

### 2. Multi-Region Deployment
- **Primary region**: Active deployment
- **Secondary region**: Standby with data replication
- **Failover**: Automated with health checks

### 3. Data Retention
- **Call logs**: 90 days (compliance requirement)
- **User data**: Until account deletion
- **Analytics**: 1 year for business intelligence

## Cost Optimization

### 1. Resource Right-sizing
- **Start conservative**: Monitor usage and scale up
- **Use spot instances**: For non-critical workloads
- **Reserved instances**: For predictable workloads

### 2. Twilio Optimization
- **Bulk SMS**: For notifications
- **Voice optimization**: Use appropriate codecs
- **Geographic routing**: Route calls efficiently

## Testing Strategy

### 1. Load Testing
```bash
# Test with realistic load
# Target: 1000 concurrent calls
# Duration: 1 hour
# Success rate: >99%
```

### 2. Chaos Engineering
- **Network failures**: Test resilience
- **Database failures**: Test failover
- **Service failures**: Test circuit breakers

## Go-Live Checklist

- [ ] Production environment configured
- [ ] Load balancer and SSL certificates set up
- [ ] Database migrations completed
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery tested
- [ ] Security audit completed
- [ ] Load testing passed
- [ ] Twilio production account activated
- [ ] Webhook URLs updated
- [ ] DNS configured
- [ ] Documentation updated

## Support & Maintenance

### 1. Incident Response
- **24/7 monitoring**: Automated alerts
- **Escalation procedures**: Defined response times
- **Post-mortems**: Learn from incidents

### 2. Regular Maintenance
- **Security updates**: Monthly patches
- **Performance tuning**: Quarterly reviews
- **Capacity planning**: Monthly analysis

This setup will handle 300k users with high availability and scalability. Start with the minimum viable configuration and scale up based on actual usage patterns. 