"""
OneVault Platform - Main FastAPI Application
===========================================

Multi-customer SaaS platform with database-per-customer isolation,
Data Vault 2.0 foundation, and industry-specific compliance.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import settings
from .core.configRegistry import ConfigRegistry
from .core.database import (
    db_manager, 
    db_router, 
    validate_database_connectivity,
    DataVaultUtils
)
from .config.configConstants import (
    CONFIG_FIELDS, 
    API_KEYS, 
    HTTP_HEADERS,
    get_nested_config_value,
    build_api_response,
    build_customer_summary
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize configuration registry
config_registry = ConfigRegistry()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-customer SaaS platform with complete database isolation",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["yourdomain.com", "*.yourdomain.com"]
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )

# Customer validation dependency
async def validate_customer_header(request: Request) -> str:
    """Validate and extract customer ID from request headers"""
    customer_id = request.headers.get(HTTP_HEADERS.CUSTOMER_ID)
    
    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail=f"Missing {HTTP_HEADERS.CUSTOMER_ID} header"
        )
    
    try:
        # Validate customer configuration exists using TypeScript config
        customer_config = await config_registry.get_customer_config(customer_id)
        if not customer_config:
            raise ValueError(f"Customer configuration not found: {customer_id}")
        return customer_id
    except Exception as e:
        logger.error(f"Customer validation failed for {customer_id}: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Customer not found: {customer_id}"
        )

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": "production" if not settings.DEBUG else "development"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including database connectivity"""
    try:
        # Check database connectivity
        db_status = await validate_database_connectivity()
        
        # Get platform configuration
        platform_config = await config_registry.get_platform_config()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "database_status": db_status,
            "features": platform_config.get("features", {}),
            "supported_industries": platform_config.get("supportedIndustries", []),
            "compliance_frameworks": platform_config.get("complianceFrameworks", [])
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@app.get("/health/customer/{customer_id}")
async def customer_health_check(customer_id: str):
    """Health check for specific customer database"""
    try:
        # Get customer configuration
        customer_config = await config_registry.get_customer_config(customer_id)
        if not customer_config:
            raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")
        
        # Validate customer database
        validation_result = await db_manager.validate_customer_database(customer_id)
        
        return {
            API_KEYS.CUSTOMER_ID: customer_id,
            API_KEYS.CUSTOMER_NAME: get_nested_config_value(
                customer_config, CONFIG_FIELDS.CUSTOMER, CONFIG_FIELDS.CUSTOMER_NAME
            ),
            "industry": get_nested_config_value(customer_config, CONFIG_FIELDS.INDUSTRY),
            API_KEYS.STATUS: "healthy" if validation_result.get(API_KEYS.DATABASE_VALID) else "unhealthy",
            API_KEYS.TIMESTAMP: datetime.utcnow().isoformat(),
            API_KEYS.DATABASE_STATUS: validation_result,
            API_KEYS.MONTHLY_COST: get_nested_config_value(
                customer_config, CONFIG_FIELDS.PRICING, CONFIG_FIELDS.PRICING_MONTHLY_TOTAL, default=0
            )
        }
    except Exception as e:
        logger.error(f"Customer health check failed for {customer_id}: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "customer_id": customer_id,
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

# Platform management endpoints
@app.get("/api/v1/platform/info")
async def platform_info():
    """Get platform information and capabilities"""
    try:
        platform_config = await config_registry.get_platform_config()
        
        return {
            "platform": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "architecture": "database-per-customer",
                "data_vault_version": "2.0"
            },
            "capabilities": {
                "industries_supported": platform_config.get("supportedIndustries", []),
                "compliance_frameworks": platform_config.get("complianceFrameworks", []),
                "features": platform_config.get("features", {})
            },
            "data_vault": {
                "hash_algorithm": settings.database.HASH_ALGORITHM,
                "record_source": settings.database.RECORD_SOURCE_SYSTEM,
                "timezone": settings.database.LOAD_DATE_TIMEZONE
            },
            "pricing": {
                "base_monthly": platform_config.get("pricing", {}).get("baseMonthly", 0),
                "per_location": platform_config.get("pricing", {}).get("perLocation", 0),
                "enterprise_discount": platform_config.get("pricing", {}).get("enterpriseDiscount", 0)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get platform info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve platform information")

@app.get("/api/v1/platform/customers")
async def list_customers():
    """List configured customers (for platform admin)"""
    try:
        customer_ids = await config_registry.get_all_customer_ids()
        customers = []
        
        for customer_id in customer_ids:
            try:
                customer_config = await config_registry.get_customer_config(customer_id)
                if customer_config:
                    customers.append({
                        API_KEYS.CUSTOMER_ID: customer_id,
                        CONFIG_FIELDS.CUSTOMER_NAME: get_nested_config_value(
                            customer_config, CONFIG_FIELDS.CUSTOMER, CONFIG_FIELDS.CUSTOMER_NAME
                        ),
                        CONFIG_FIELDS.INDUSTRY: get_nested_config_value(customer_config, CONFIG_FIELDS.INDUSTRY),
                        API_KEYS.STATUS: "active" if get_nested_config_value(
                            customer_config, CONFIG_FIELDS.CUSTOMER, CONFIG_FIELDS.CUSTOMER_ACTIVE, default=True
                        ) else "inactive",
                        API_KEYS.LOCATION_COUNT: len(get_nested_config_value(
                            customer_config, CONFIG_FIELDS.LOCATIONS, default=[]
                        )),
                        API_KEYS.MONTHLY_COST: get_nested_config_value(
                            customer_config, CONFIG_FIELDS.PRICING, CONFIG_FIELDS.PRICING_MONTHLY_TOTAL, default=0
                        ),
                        "compliance_frameworks": get_nested_config_value(
                            customer_config, CONFIG_FIELDS.COMPLIANCE, CONFIG_FIELDS.COMPLIANCE_FRAMEWORKS, default=[]
                        )
                    })
            except Exception as e:
                logger.warning(f"Failed to load config for customer {customer_id}: {e}")
                continue
        
        return build_api_response(
            data={
                "customers": customers,
                API_KEYS.TOTAL: len(customers)
            }
        )
    except Exception as e:
        logger.error(f"Failed to list customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve customer list")

# Customer-specific endpoints
@app.get("/api/v1/customer/config")
async def get_customer_config_endpoint(customer_id: str = Depends(validate_customer_header)):
    """Get customer configuration and capabilities"""
    try:
        customer_config = await config_registry.get_customer_config(customer_id)
        
        # Return safe configuration (no sensitive data)
        locations_data = get_nested_config_value(customer_config, CONFIG_FIELDS.LOCATIONS, default=[])
        
        return build_api_response(
            data={
                API_KEYS.CUSTOMER_ID: customer_id,
                CONFIG_FIELDS.CUSTOMER_NAME: get_nested_config_value(
                    customer_config, CONFIG_FIELDS.CUSTOMER, CONFIG_FIELDS.CUSTOMER_NAME
                ),
                CONFIG_FIELDS.INDUSTRY: get_nested_config_value(customer_config, CONFIG_FIELDS.INDUSTRY),
                "enabled_features": get_nested_config_value(customer_config, CONFIG_FIELDS.FEATURES, default={}),
                "compliance_frameworks": get_nested_config_value(
                    customer_config, CONFIG_FIELDS.COMPLIANCE, CONFIG_FIELDS.COMPLIANCE_FRAMEWORKS, default=[]
                ),
                CONFIG_FIELDS.BRANDING: get_nested_config_value(customer_config, CONFIG_FIELDS.BRANDING, default={}),
                CONFIG_FIELDS.LOCATIONS: [
                    {
                        CONFIG_FIELDS.LOCATION_ID: loc.get(CONFIG_FIELDS.LOCATION_ID),
                        CONFIG_FIELDS.LOCATION_NAME: loc.get(CONFIG_FIELDS.LOCATION_NAME),
                        CONFIG_FIELDS.LOCATION_ADDRESS: loc.get(CONFIG_FIELDS.LOCATION_ADDRESS),
                        CONFIG_FIELDS.LOCATION_ACTIVE: loc.get(CONFIG_FIELDS.LOCATION_ACTIVE, True)
                    }
                    for loc in locations_data
                ],
                CONFIG_FIELDS.PRICING: {
                    CONFIG_FIELDS.PRICING_MONTHLY_TOTAL: get_nested_config_value(
                        customer_config, CONFIG_FIELDS.PRICING, CONFIG_FIELDS.PRICING_MONTHLY_TOTAL, default=0
                    ),
                    CONFIG_FIELDS.PRICING_BASE_COST: get_nested_config_value(
                        customer_config, CONFIG_FIELDS.PRICING, CONFIG_FIELDS.PRICING_BASE_COST, default=0
                    ),
                    CONFIG_FIELDS.PRICING_LOCATION_COST: get_nested_config_value(
                        customer_config, CONFIG_FIELDS.PRICING, CONFIG_FIELDS.PRICING_LOCATION_COST, default=0
                    )
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to get customer config for {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve customer configuration")

@app.get("/api/v1/customer/branding")
async def get_customer_branding(customer_id: str = Depends(validate_customer_header)):
    """Get customer branding configuration"""
    try:
        customer_config = await config_registry.get_customer_config(customer_id)
        branding = customer_config.get("branding", {})
        
        return {
            "customer_id": customer_id,
            "branding": branding,
            "css_variables": await config_registry.get_customer_branding_css(customer_id),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get customer branding for {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve customer branding")

@app.get("/api/v1/customer/locations")
async def get_customer_locations(customer_id: str = Depends(validate_customer_header)):
    """Get customer locations with business hours and status"""
    try:
        customer_config = await config_registry.get_customer_config(customer_id)
        locations = customer_config.get("locations", [])
        
        # Enhance locations with current status
        enhanced_locations = []
        for location in locations:
            enhanced_location = {
                **location,
                "is_open_now": await config_registry.is_location_open_now(customer_id, location.get("id"))
            }
            enhanced_locations.append(enhanced_location)
        
        return {
            "customer_id": customer_id,
            "locations": enhanced_locations,
            "total_locations": len(enhanced_locations),
            "active_locations": len([loc for loc in enhanced_locations if loc.get("isActive", True)]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get customer locations for {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve customer locations")

@app.get("/api/v1/customer/database/validate")
async def validate_customer_database_endpoint(customer_id: str = Depends(validate_customer_header)):
    """Validate customer's database structure"""
    try:
        validation_result = await db_manager.validate_customer_database(customer_id)
        return validation_result
    except Exception as e:
        logger.error(f"Database validation failed for {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Database validation failed")

# Data Vault 2.0 utility endpoints
@app.post("/api/v1/utils/hash")
async def generate_hash(data: Dict[str, Any]):
    """Generate Data Vault 2.0 hash for given data"""
    try:
        values = data.get("values", [])
        if not values:
            raise HTTPException(status_code=400, detail="No values provided for hashing")
        
        hash_result = DataVaultUtils.hash_binary(*values)
        
        return {
            "hash_binary": hash_result.hex(),
            "input_values": values,
            "algorithm": settings.database.HASH_ALGORITHM,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Hash generation failed: {e}")
        raise HTTPException(status_code=500, detail="Hash generation failed")

@app.get("/api/v1/utils/current-load-date")
async def get_current_load_date():
    """Get current load date in Data Vault 2.0 format"""
    return {
        "load_date": DataVaultUtils.current_load_date().isoformat(),
        "timezone": settings.database.LOAD_DATE_TIMEZONE,
        "record_source": DataVaultUtils.get_record_source()
    }

# Configuration management endpoints
@app.post("/api/v1/config/reload")
async def reload_configurations():
    """Reload all customer configurations (admin only)"""
    try:
        await config_registry.reload_all_configs()
        return {
            "status": "success",
            "message": "All configurations reloaded successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Configuration reload failed: {e}")
        raise HTTPException(status_code=500, detail="Configuration reload failed")

@app.get("/api/v1/config/validate/{customer_id}")
async def validate_customer_config(customer_id: str):
    """Validate specific customer configuration"""
    try:
        validation_result = await config_registry.validate_customer_config(customer_id)
        return {
            "customer_id": customer_id,
            "validation_result": validation_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Configuration validation failed for {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Configuration validation failed")

# Site tracking endpoint
@app.post("/api/v1/track")
async def track_site_event(
    request: Request,
    event_data: Dict[str, Any],
    customer_id: str = Depends(validate_customer_header)
):
    """Site tracking endpoint - what customers call"""
    try:
        # Get API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")
        
        api_token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Call your database function through db_manager
        result = await db_manager.execute_function(
            customer_id,
            "api.track_site_event",
            {
                "p_api_token": api_token,
                "p_session_id": event_data.get("session_id"),
                "p_page_url": event_data.get("page_url"),
                "p_event_type": event_data.get("event_type", "page_view"),
                "p_event_data": event_data.get("event_data"),
                "p_user_agent": request.headers.get("User-Agent"),
                "p_ip_address": request.client.host,
                "p_referrer_url": event_data.get("referrer_url")
            }
        )
        
        return {"success": True, "event_id": result.get("event_id")}
        
    except Exception as e:
        logger.error(f"Site tracking failed: {e}")
        raise HTTPException(status_code=500, detail="Event tracking failed")

# Middleware for request logging and audit
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all requests for audit purposes"""
    start_time = datetime.utcnow()
    
    # Log request
    customer_id = request.headers.get(HTTP_HEADERS.CUSTOMER_ID, "unknown")
    logger.info(f"Request: {request.method} {request.url.path} - Customer: {customer_id}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"Response: {response.status_code} - "
        f"Customer: {customer_id} - "
        f"Time: {process_time:.3f}s"
    )
    
    # Add audit headers
    response.headers[HTTP_HEADERS.REQUEST_ID] = f"{start_time.timestamp()}"
    response.headers[HTTP_HEADERS.PROCESS_TIME] = f"{process_time:.3f}"
    
    return response

# Application startup
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Starting OneVault Platform...")
    
    try:
        # Validate system database connectivity
        system_session = db_manager.get_system_session()
        system_session.execute("SELECT 1")
        system_session.close()
        logger.info("✅ System database connection validated")
        
        # Initialize configuration registry
        await config_registry.initialize()
        logger.info("✅ TypeScript configuration registry initialized")
        
        # Load and validate all customer configurations
        customer_ids = await config_registry.get_all_customer_ids()
        logger.info(f"✅ Loaded {len(customer_ids)} customer configurations")
        
        # Log platform configuration
        platform_config = await config_registry.get_platform_config()
        logger.info(f"✅ Platform: {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"✅ Supported industries: {platform_config.get('supportedIndustries', [])}")
        logger.info(f"✅ Compliance frameworks: {platform_config.get('complianceFrameworks', [])}")
        
        logger.info("🚀 OneVault Platform startup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down OneVault Platform...")
    
    # Close database connections
    # The connection pools will be cleaned up automatically
    
    logger.info("👋 OneVault Platform shutdown completed")

# Development server runner
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

# Vercel handler
handler = app 