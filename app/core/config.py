"""
Configuration management for OneVault platform.
Integrates with TypeScript configuration files as single source of truth.
"""
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Database Configuration
    SYSTEM_DATABASE_URL: str = Field(..., env="SYSTEM_DATABASE_URL")
    CUSTOMER_DATABASE_BASE_URL: str = Field(..., env="CUSTOMER_DATABASE_BASE_URL") 
    
    # Security Configuration  
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ENCRYPTION_KEY: str = Field(..., env="ENCRYPTION_KEY")
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    # Application Configuration
    APP_NAME: str = Field(default="OneVault Platform", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # CORS Configuration
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    CORS_ORIGINS: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Redis Configuration (for caching)
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # TypeScript Config Integration
    TYPESCRIPT_CONFIG_PATH: str = Field(
        default="backend/app/core/configRegistry.ts",
        env="TYPESCRIPT_CONFIG_PATH"
    )
    NODE_PATH: str = Field(default="node", env="NODE_PATH")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()

class TypeScriptConfigBridge:
    """Bridge to access TypeScript configuration files from Python."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config_cache: Dict[str, Any] = {}
        self._last_cache_time = 0
        
    def _execute_typescript_function(self, function_call: str) -> Any:
        """Execute TypeScript function and return result."""
        try:
            # Parse function call to extract function name and args
            if '(' in function_call:
                func_name = function_call.split('(')[0]
                # Extract arguments from function call
                args_str = function_call[function_call.find('(')+1:function_call.rfind(')')]
                args = []
                if args_str.strip():
                    # Simple argument parsing (handles quoted strings)
                    import re
                    args = re.findall(r"'([^']*)'|\"([^\"]*)\"|([^,\s]+)", args_str)
                    args = [match[0] or match[1] or match[2] for match in args]
            else:
                func_name = function_call
                args = []
            
            # Execute with our Node.js bridge
            bridge_path = Path("backend/app/utils/configBridge.js")
            cmd = [self.settings.NODE_PATH, str(bridge_path), func_name] + args
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return json.loads(result.stdout.strip())
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error executing TypeScript function {function_call}: {e}")
            return None
    
    def get_customer_config(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer configuration from TypeScript config."""
        cache_key = f"customer_config_{customer_id}"
        
        if cache_key in self.config_cache:
            return self.config_cache[cache_key]
            
        config = self._execute_typescript_function(f"getCustomerConfig('{customer_id}')")
        
        if config:
            self.config_cache[cache_key] = config
            
        return config
    
    def get_customer_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get customer configuration by domain."""
        return self._execute_typescript_function(f"getCustomerByDomain('{domain}')")
    
    def get_all_customer_ids(self) -> List[str]:
        """Get all registered customer IDs."""
        result = self._execute_typescript_function("getAllCustomerIds()")
        return result if result else []
    
    def is_valid_customer(self, customer_id: str) -> bool:
        """Check if customer ID is valid."""
        result = self._execute_typescript_function(f"isValidCustomer('{customer_id}')")
        return bool(result) if result is not None else False
    
    def get_customer_compliance_frameworks(self, customer_id: str) -> List[str]:
        """Get compliance frameworks for customer."""
        result = self._execute_typescript_function(f"getCustomerComplianceFrameworks('{customer_id}')")
        return result if result else []
    
    def get_customer_branding_vars(self, customer_id: str) -> Dict[str, str]:
        """Get customer branding CSS variables."""
        result = self._execute_typescript_function(f"getCustomerBrandingVars('{customer_id}')")
        return result if result else {}
    
    def get_customer_tenant_by_subdomain(self, customer_id: str, subdomain: str) -> Optional[Dict[str, Any]]:
        """Get customer tenant configuration by subdomain."""
        return self._execute_typescript_function(f"getCustomerTenantBySubdomain('{customer_id}', '{subdomain}')")
    
    def clear_cache(self):
        """Clear configuration cache."""
        self.config_cache.clear()
        self._last_cache_time = 0

# Global instances
settings = get_settings()
ts_config = TypeScriptConfigBridge(settings)

class CustomerConfigManager:
    """Manager for customer-specific configurations with TypeScript integration."""
    
    def __init__(self):
        self.ts_bridge = ts_config
        
    def get_customer_config(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get complete customer configuration."""
        return self.ts_bridge.get_customer_config(customer_id)
    
    def get_customer_database_url(self, customer_id: str) -> str:
        """Generate customer-specific database URL."""
        base_url = settings.CUSTOMER_DATABASE_BASE_URL
        # Remove trailing slash and add customer database name
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        return f"{base_url}/onevault_{customer_id.lower()}"
    
    def get_customer_security_config(self, customer_id: str) -> Dict[str, Any]:
        """Get customer security configuration."""
        config = self.get_customer_config(customer_id)
        if not config:
            return self._get_default_security_config()
            
        return config.get('security', self._get_default_security_config())
    
    def get_customer_compliance_config(self, customer_id: str) -> Dict[str, Any]:
        """Get customer compliance configuration."""
        config = self.get_customer_config(customer_id)
        if not config:
            return self._get_default_compliance_config()
            
        return config.get('compliance', self._get_default_compliance_config())
    
    def get_customer_branding(self, customer_id: str) -> Dict[str, Any]:
        """Get customer branding configuration."""
        config = self.get_customer_config(customer_id)
        if not config:
            return self._get_default_branding_config()
            
        return config.get('branding', self._get_default_branding_config())
    
    def get_customer_locations(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer locations."""
        config = self.get_customer_config(customer_id)
        if not config:
            return []
            
        return config.get('locations', [])
    
    def get_customer_tenants(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer tenants."""
        config = self.get_customer_config(customer_id)
        if not config:
            return []
            
        return config.get('tenants', [])
    
    def is_hipaa_enabled(self, customer_id: str) -> bool:
        """Check if HIPAA compliance is enabled for customer."""
        compliance_config = self.get_customer_compliance_config(customer_id)
        return compliance_config.get('hipaa', {}).get('enabled', False)
    
    def is_gdpr_enabled(self, customer_id: str) -> bool:
        """Check if GDPR compliance is enabled for customer."""
        compliance_config = self.get_customer_compliance_config(customer_id)
        return compliance_config.get('gdpr', {}).get('enabled', False)
    
    def is_sox_enabled(self, customer_id: str) -> bool:
        """Check if SOX compliance is enabled for customer."""
        compliance_config = self.get_customer_compliance_config(customer_id)
        return compliance_config.get('sox', {}).get('enabled', False)
    
    def get_customer_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get customer configuration by domain."""
        return self.ts_bridge.get_customer_by_domain(domain)
    
    def get_all_customer_ids(self) -> List[str]:
        """Get all registered customer IDs."""
        return self.ts_bridge.get_all_customer_ids()
    
    def _get_default_security_config(self) -> Dict[str, Any]:
        """Get default security configuration."""
        return {
            "authentication": {
                "mfaRequired": True,
                "passwordPolicy": {
                    "minLength": 12,
                    "requireUppercase": True,
                    "requireLowercase": True,
                    "requireNumbers": True,
                    "requireSpecialChars": True,
                    "maxAge": 90
                },
                "sessionTimeout": 30,
                "maxFailedAttempts": 3,
                "lockoutDuration": 15
            },
            "encryption": {
                "algorithm": "AES-256-GCM",
                "keyRotationDays": 90,
                "dataAtRest": True,
                "dataInTransit": True
            },
            "audit": {
                "logAllAccess": True,
                "retentionDays": 2555,
                "realTimeAlerts": True
            }
        }
    
    def _get_default_compliance_config(self) -> Dict[str, Any]:
        """Get default compliance configuration."""
        return {
            "requiredFrameworks": ["HIPAA"],
            "hipaa": {
                "enabled": True,
                "baaRequired": True,
                "auditRetentionYears": 6,
                "encryptionRequired": True
            },
            "gdpr": {
                "enabled": False,
                "dataRetentionDays": 0,
                "rightToBeForgitten": False,
                "consentRequired": False
            },
            "sox": {
                "enabled": False,
                "financialReportingRequired": False,
                "controlTestingRequired": False
            }
        }
    
    def _get_default_branding_config(self) -> Dict[str, Any]:
        """Get default branding configuration."""
        return {
            "companyName": "OneVault Customer",
            "displayName": "OneVault Platform",
            "colors": {
                "primary": "#2D5AA0",
                "secondary": "#E8B931",
                "accent": "#F5F5F5",
                "background": "#FFFFFF",
                "text": "#2C3E50"
            },
            "fonts": {
                "primary": "Arial, sans-serif"
            }
        }

# Global customer config manager
customer_config_manager = CustomerConfigManager()

# Convenience functions for backward compatibility and ease of use
def get_customer_config(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get customer configuration."""
    return customer_config_manager.get_customer_config(customer_id)

def get_customer_database_url(customer_id: str) -> str:
    """Get customer database URL."""
    return customer_config_manager.get_customer_database_url(customer_id)

def is_hipaa_customer(customer_id: str) -> bool:
    """Check if customer requires HIPAA compliance."""
    return customer_config_manager.is_hipaa_enabled(customer_id)

def get_customer_by_domain(domain: str) -> Optional[Dict[str, Any]]:
    """Get customer by domain."""
    return customer_config_manager.get_customer_by_domain(domain)

def get_all_customer_ids() -> List[str]:
    """Get all customer IDs."""
    return customer_config_manager.get_all_customer_ids() 