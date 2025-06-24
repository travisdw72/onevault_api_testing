"""
Configuration Constants for OneVault Platform
===========================================

Centralized constants for all configuration field names, API keys, 
and data structure keys used throughout the application.

Following the same pattern as headerConfig.ts with centralized constants.
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass(frozen=True)
class ConfigFieldNames:
    """Configuration field names used throughout the application."""
    
    # Customer Configuration Root Fields
    CUSTOMER = "customer"
    INDUSTRY = "industry"
    LOCATIONS = "locations"
    PRICING = "pricing"
    BRANDING = "branding"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    TENANTS = "tenants"
    ANALYTICS = "analytics"
    INTEGRATIONS = "integrations"
    FEATURES = "features"
    
    # Customer Info Fields
    CUSTOMER_NAME = "name"
    CUSTOMER_ID = "id"
    CUSTOMER_EMAIL = "contactEmail"
    CUSTOMER_PHONE = "contactPhone"
    CUSTOMER_ACTIVE = "isActive"
    CUSTOMER_DOMAIN = "domain"
    
    # Pricing Fields
    PRICING_BASE_PLAN = "basePlan"
    PRICING_ADD_ONS = "addOns"
    PRICING_CUSTOMIZATION = "customization"
    PRICING_BILLING = "billing"
    PRICING_MONTHLY_PRICE = "monthlyPrice"
    PRICING_ANNUAL_PRICE = "annualPrice"
    PRICING_MONTHLY_TOTAL = "monthlyTotal"
    PRICING_BASE_COST = "baseCost"
    PRICING_LOCATION_COST = "locationCost"
    PRICING_CURRENCY = "currency"
    
    # Location Fields
    LOCATION_ID = "id"
    LOCATION_NAME = "name"
    LOCATION_ADDRESS = "address"
    LOCATION_ACTIVE = "isActive"
    LOCATION_BUSINESS_HOURS = "businessHours"
    LOCATION_CONTACT = "contact"
    LOCATION_TIMEZONE = "timezone"
    
    # Branding Fields
    BRANDING_PRIMARY_COLOR = "primaryColor"
    BRANDING_SECONDARY_COLOR = "secondaryColor"
    BRANDING_ACCENT_COLOR = "accentColor"
    BRANDING_LOGO_URL = "logoUrl"
    BRANDING_FONT_FAMILY = "fontFamily"
    BRANDING_COMPANY_NAME = "companyName"
    BRANDING_THEME = "theme"
    
    # Compliance Fields
    COMPLIANCE_FRAMEWORKS = "frameworks"
    COMPLIANCE_HIPAA = "hipaa"
    COMPLIANCE_GDPR = "gdpr"
    COMPLIANCE_SOX = "sox"
    COMPLIANCE_PCI_DSS = "pciDss"
    COMPLIANCE_ENABLED = "enabled"
    COMPLIANCE_SETTINGS = "settings"
    
    # Security Fields
    SECURITY_AUTHENTICATION = "authentication"
    SECURITY_ENCRYPTION = "encryption"
    SECURITY_AUDIT = "audit"
    SECURITY_MFA_REQUIRED = "mfaRequired"
    SECURITY_PASSWORD_POLICY = "passwordPolicy"
    
    # Tenant Fields
    TENANT_ID = "id"
    TENANT_NAME = "name"
    TENANT_DOMAIN = "domain"
    TENANT_SUBDOMAIN = "subdomain"
    TENANT_ACTIVE = "isActive"
    TENANT_USERS = "users"
    TENANT_FEATURES = "features"
    
    # Business Hours Fields
    HOURS_OPEN = "open"
    HOURS_CLOSE = "close"
    HOURS_CLOSED = "closed"
    
    # Feature Fields
    FEATURES_ENABLED = "enabled"
    FEATURES_DISABLED = "disabled"
    FEATURES_BETA = "beta"

@dataclass(frozen=True)
class APIResponseKeys:
    """Standard API response field names."""
    
    # Standard Response Fields
    STATUS = "status"
    MESSAGE = "message"
    DATA = "data"
    ERROR = "error"
    TIMESTAMP = "timestamp"
    
    # Pagination Fields
    TOTAL = "total"
    PAGE = "page"
    PAGE_SIZE = "pageSize"
    ITEMS = "items"
    
    # Customer Response Fields
    CUSTOMER_ID = "customer_id"
    CUSTOMER_NAME = "customer_name"
    MONTHLY_COST = "monthly_cost"
    ANNUAL_COST = "annual_cost"
    LOCATION_COUNT = "location_count"
    
    # Health Check Fields
    DATABASE_STATUS = "database_status"
    DATABASE_VALID = "database_valid"
    VALIDATION_RESULT = "validation_result"
    
    # Configuration Fields
    CONFIG_SUMMARY = "config_summary"
    VALIDATION_ERRORS = "errors"
    VALIDATION_WARNINGS = "warnings"
    VALIDATION_VALID = "valid"

@dataclass(frozen=True)
class DatabaseFieldNames:
    """Database field names for Data Vault 2.0 structures."""
    
    # Hash Keys
    TENANT_HK = "tenant_hk"
    USER_HK = "user_hk"
    SESSION_HK = "session_hk"
    CUSTOMER_HK = "customer_hk"
    
    # Business Keys
    TENANT_BK = "tenant_bk"
    USER_BK = "user_bk"
    SESSION_BK = "session_bk"
    CUSTOMER_BK = "customer_bk"
    
    # Temporal Fields
    LOAD_DATE = "load_date"
    LOAD_END_DATE = "load_end_date"
    HASH_DIFF = "hash_diff"
    RECORD_SOURCE = "record_source"
    
    # Audit Fields
    CREATED_BY = "created_by"
    MODIFIED_BY = "modified_by"
    CREATED_DATE = "created_date"
    MODIFIED_DATE = "modified_date"

@dataclass(frozen=True)
class HTTPHeaderNames:
    """HTTP header names used in the application."""
    
    CUSTOMER_ID = "X-Customer-ID"
    TENANT_ID = "X-Tenant-ID"
    REQUEST_ID = "X-Request-ID"
    PROCESS_TIME = "X-Process-Time"
    API_VERSION = "X-API-Version"
    CONTENT_TYPE = "Content-Type"
    AUTHORIZATION = "Authorization"

@dataclass(frozen=True)
class CSSVariableNames:
    """CSS variable names for theming."""
    
    PRIMARY_COLOR = "--primary-color"
    SECONDARY_COLOR = "--secondary-color"
    ACCENT_COLOR = "--accent-color"
    BACKGROUND_COLOR = "--background-color"
    TEXT_COLOR = "--text-color"
    FONT_FAMILY = "--font-family"
    LOGO_URL = "--logo-url"

@dataclass(frozen=True)
class IndustryTypes:
    """Supported industry types."""
    
    SPA_WELLNESS = "spa_wellness"
    FINANCIAL_SERVICES = "financial_services"
    EQUESTRIAN = "equestrian"
    PROPERTY_MANAGEMENT = "property_management"
    HEALTHCARE = "healthcare"

@dataclass(frozen=True)
class ComplianceFrameworks:
    """Supported compliance frameworks."""
    
    HIPAA = "hipaa"
    HITECH = "hitech"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    CCPA = "ccpa"
    GLBA = "glba"

@dataclass(frozen=True)
class PlatformFeatures:
    """Platform feature flags."""
    
    MULTI_TENANT = "multiTenant"
    WHITE_LABEL = "whiteLabel"
    INDUSTRY_MODULES = "industryModules"
    DATA_VAULT_2 = "dataVault2"
    AUDIT_LOGGING = "auditLogging"
    ENCRYPTION_AT_REST = "encryptionAtRest"

# Global instances for easy access
CONFIG_FIELDS = ConfigFieldNames()
API_KEYS = APIResponseKeys()
DB_FIELDS = DatabaseFieldNames()
HTTP_HEADERS = HTTPHeaderNames()
CSS_VARS = CSSVariableNames()
INDUSTRIES = IndustryTypes()
COMPLIANCE = ComplianceFrameworks()
FEATURES = PlatformFeatures()

# Helper functions for accessing nested configuration values
def get_nested_config_value(config: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely get nested configuration values using constant field names.
    
    Example:
        get_nested_config_value(config, CONFIG_FIELDS.PRICING, CONFIG_FIELDS.PRICING_MONTHLY_TOTAL)
    """
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def build_api_response(
    status: str = "success",
    data: Any = None,
    message: str = None,
    error: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Build standardized API response using constant field names.
    
    Example:
        build_api_response(
            status="success",
            data=customer_data,
            message="Customer retrieved successfully"
        )
    """
    from datetime import datetime
    
    response = {
        API_KEYS.STATUS: status,
        API_KEYS.TIMESTAMP: datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response[API_KEYS.DATA] = data
    
    if message:
        response[API_KEYS.MESSAGE] = message
    
    if error:
        response[API_KEYS.ERROR] = error
    
    # Add any additional fields
    response.update(kwargs)
    
    return response

def build_customer_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build customer summary using constant field names.
    
    Example:
        summary = build_customer_summary(customer_config)
    """
    return {
        API_KEYS.CUSTOMER_NAME: get_nested_config_value(
            config, CONFIG_FIELDS.CUSTOMER, CONFIG_FIELDS.CUSTOMER_NAME
        ),
        "industry": get_nested_config_value(config, CONFIG_FIELDS.INDUSTRY),
        API_KEYS.LOCATION_COUNT: len(get_nested_config_value(
            config, CONFIG_FIELDS.LOCATIONS, default=[]
        )),
        API_KEYS.MONTHLY_COST: get_nested_config_value(
            config, CONFIG_FIELDS.PRICING, CONFIG_FIELDS.PRICING_MONTHLY_TOTAL, default=0
        )
    }

def get_branding_css_vars(branding_config: Dict[str, Any]) -> Dict[str, str]:
    """
    Convert branding configuration to CSS variables using constant names.
    
    Example:
        css_vars = get_branding_css_vars(config['branding'])
    """
    css_vars = {}
    
    if CONFIG_FIELDS.BRANDING_PRIMARY_COLOR in branding_config:
        css_vars[CSS_VARS.PRIMARY_COLOR] = branding_config[CONFIG_FIELDS.BRANDING_PRIMARY_COLOR]
    
    if CONFIG_FIELDS.BRANDING_SECONDARY_COLOR in branding_config:
        css_vars[CSS_VARS.SECONDARY_COLOR] = branding_config[CONFIG_FIELDS.BRANDING_SECONDARY_COLOR]
    
    if CONFIG_FIELDS.BRANDING_ACCENT_COLOR in branding_config:
        css_vars[CSS_VARS.ACCENT_COLOR] = branding_config[CONFIG_FIELDS.BRANDING_ACCENT_COLOR]
    
    if CONFIG_FIELDS.BRANDING_LOGO_URL in branding_config:
        css_vars[CSS_VARS.LOGO_URL] = f"url('{branding_config[CONFIG_FIELDS.BRANDING_LOGO_URL]}')"
    
    if CONFIG_FIELDS.BRANDING_FONT_FAMILY in branding_config:
        css_vars[CSS_VARS.FONT_FAMILY] = branding_config[CONFIG_FIELDS.BRANDING_FONT_FAMILY]
    
    return css_vars

# Validation helpers
def validate_required_config_fields(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate that required configuration fields are present.
    
    Returns:
        tuple: (is_valid, list_of_missing_fields)
    """
    required_fields = [
        CONFIG_FIELDS.CUSTOMER,
        CONFIG_FIELDS.INDUSTRY,
        CONFIG_FIELDS.LOCATIONS,
        CONFIG_FIELDS.PRICING
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in config:
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields

def get_compliance_frameworks_list(config: Dict[str, Any]) -> list[str]:
    """
    Get list of enabled compliance frameworks using constant field names.
    
    Example:
        frameworks = get_compliance_frameworks_list(customer_config)
    """
    return get_nested_config_value(
        config, 
        CONFIG_FIELDS.COMPLIANCE, 
        CONFIG_FIELDS.COMPLIANCE_FRAMEWORKS, 
        default=[]
    ) 