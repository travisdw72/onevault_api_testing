# OneVault API

Multi-tenant business analytics and site tracking API built with FastAPI and Data Vault 2.0 architecture.

## Features

- 🏢 **Multi-tenant isolation** - Complete data separation per customer
- 📊 **Site tracking** - Universal analytics for any business type
- 🔒 **Enterprise security** - HIPAA/GDPR compliant
- ⚡ **High performance** - Built on FastAPI with async support
- 🎯 **Industry agnostic** - Works for healthcare, retail, services, etc.

## Quick Start

### For Customers

Add our tracking to your website:

```javascript
// Add to your website
fetch('https://your-api-domain.com/api/v1/track', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your_api_token',
    'X-Customer-ID': 'your_customer_id'
  },
  body: JSON.stringify({
    session_id: 'user_session_123',
    page_url: window.location.href,
    event_type: 'page_view',
    event_data: { source: 'organic' }
  })
})
```

### For Developers

Deploy your own instance:

```bash
# Clone and install
git clone https://github.com/theonespaoregon/onevault-api.git
cd onevault-api
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your database URL and secrets

# Run locally
uvicorn app.main:app --reload

# Deploy to Vercel
vercel
```

## API Endpoints

- `POST /api/v1/track` - Track site events
- `GET /health` - Health check
- `GET /api/v1/platform/info` - Platform capabilities

## Environment Variables

Required for deployment:

- `SYSTEM_DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Application secret key
- `DEBUG` - Set to `false` for production

## Architecture

Built on Data Vault 2.0 methodology for:
- Complete audit trails
- Historical data tracking
- Scalable multi-tenant design
- Regulatory compliance (HIPAA, GDPR)

## Support

For API access and customer onboarding, contact: travis@theonespaoregon.com

## License

Proprietary - OneVault Platform 