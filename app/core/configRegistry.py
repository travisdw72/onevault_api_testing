"""
Configuration Registry for OneVault Platform
==========================================

Python wrapper around TypeScript configuration system providing
async interface for FastAPI integration.
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import logging

from .config import settings, TypeScriptConfigBridge
from ..config.configConstants import (
    CONFIG_FIELDS, 
    API_KEYS, 
    CSS_VARS,
    get_nested_config_value,
    get_branding_css_vars,
    validate_required_config_fields
)

logger = logging.getLogger(__name__)

class ConfigRegistry:
    """
    Async configuration registry that interfaces with TypeScript configs.
    Provides caching, validation, and helper functions for the FastAPI application.
    """
    
    def __init__(self):
        self.ts_bridge = TypeScriptConfigBridge(settings)
        self._initialized = False
        self._platform_config_cache: Optional[Dict[str, Any]] = None
        self._customer_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamp = datetime.utcnow()
        
    async def initialize(self) -> None:
        """Initialize the configuration registry."""
        try:
            # Test TypeScript bridge connectivity
            test_result = await self._execute_async_ts_function("getAllCustomerIds()")
            if test_result is not None:
                self._initialized = True
                logger.info("✅ ConfigRegistry initialized successfully")
            else:
                raise Exception("Failed to connect to TypeScript configuration system")
        except Exception as e:
            logger.error(f"❌ ConfigRegistry initialization failed: {e}")
            raise
    
    async def _execute_async_ts_function(self, function_call: str) -> Any:
        """Execute TypeScript function asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.ts_bridge._execute_typescript_function, 
            function_call
        )
    
    async def get_platform_config(self) -> Dict[str, Any]:
        """Get platform-wide configuration."""
        if self._platform_config_cache is None:
            # Load platform configuration from TypeScript
            platform_config = await self._execute_async_ts_function("getPlatformConfig()")
            
            if platform_config is None:
                # Fallback to default platform config
                platform_config = {
                    "supportedIndustries": [
                        "spa_wellness",
                        "financial_services", 
                        "equestrian",
                        "property_management",
                        "healthcare"
                    ],
                    "complianceFrameworks": [
                        "hipaa", "hitech", "sox", "pci_dss", 
                        "gdpr", "ccpa", "glba"
                    ],
                    "features": {
                        "multiTenant": True,
                        "whiteLabel": True,
                        "industryModules": True,
                        "dataVault2": True,
                        "auditLogging": True,
                        "encryptionAtRest": True
                    },
                    "pricing": {
                        "baseMonthly": 4999,
                        "perLocation": 299,
                        "enterpriseDiscount": 0.15
                    }
                }
            
            self._platform_config_cache = platform_config
            
        return self._platform_config_cache
    
    async def get_customer_config(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer configuration with caching."""
        cache_key = f"customer_{customer_id}"
        
        # Check cache first
        if cache_key in self._customer_cache:
            cached_config = self._customer_cache[cache_key]
            # Check if cache is still valid (5 minutes)
            if (datetime.utcnow() - self._cache_timestamp).seconds < 300:
                return cached_config
        
        # Load from TypeScript config
        config = await self._execute_async_ts_function(f"getCustomerConfig('{customer_id}')")
        
        if config:
            self._customer_cache[cache_key] = config
            self._cache_timestamp = datetime.utcnow()
        
        return config
    
    async def get_all_customer_ids(self) -> List[str]:
        """Get all registered customer IDs."""
        result = await self._execute_async_ts_function("getAllCustomerIds()")
        return result if result else []
    
    async def get_customer_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get customer configuration by domain."""
        return await self._execute_async_ts_function(f"getCustomerByDomain('{domain}')")
    
    async def validate_customer_config(self, customer_id: str) -> Dict[str, Any]:
        """Validate customer configuration."""
        try:
            config = await self.get_customer_config(customer_id)
            
            if not config:
                return {
                    API_KEYS.VALIDATION_VALID: False,
                    API_KEYS.VALIDATION_ERRORS: [f"Customer configuration not found: {customer_id}"],
                    API_KEYS.VALIDATION_WARNINGS: []
                }
            
            errors = []
            warnings = []
            
            # Validate required fields using constants
            is_valid, missing_fields = validate_required_config_fields(config)
            if not is_valid:
                errors.extend([f"Missing required field: {field}" for field in missing_fields])
            
            # Validate customer info
            customer_info = get_nested_config_value(config, CONFIG_FIELDS.CUSTOMER, default={})
            if customer_info:
                if not customer_info.get(CONFIG_FIELDS.CUSTOMER_NAME):
                    errors.append("Customer name is required")
                if not customer_info.get(CONFIG_FIELDS.CUSTOMER_EMAIL):
                    warnings.append("Customer contact email not specified")
            
            # Validate locations
            locations = get_nested_config_value(config, CONFIG_FIELDS.LOCATIONS, default=[])
            if not locations:
                warnings.append("No locations configured")
            else:
                for i, location in enumerate(locations):
                    if not location.get(CONFIG_FIELDS.LOCATION_NAME):
                        errors.append(f"Location {i+1} missing name")
                    if not location.get(CONFIG_FIELDS.LOCATION_ADDRESS):
                        warnings.append(f"Location {i+1} missing address")
            
            # Validate pricing
            pricing = get_nested_config_value(config, CONFIG_FIELDS.PRICING, default={})
            if pricing and not pricing.get(CONFIG_FIELDS.PRICING_MONTHLY_TOTAL):
                errors.append("Monthly total pricing not calculated")
            
            return {
                API_KEYS.VALIDATION_VALID: len(errors) == 0,
                API_KEYS.VALIDATION_ERRORS: errors,
                API_KEYS.VALIDATION_WARNINGS: warnings,
                API_KEYS.CONFIG_SUMMARY: {
                    API_KEYS.CUSTOMER_NAME: get_nested_config_value(
                        config, CONFIG_FIELDS.CUSTOMER, CONFIG_FIELDS.CUSTOMER_NAME
                    ),
                    CONFIG_FIELDS.INDUSTRY: get_nested_config_value(config, CONFIG_FIELDS.INDUSTRY),
                    API_KEYS.LOCATION_COUNT: len(locations),
                    API_KEYS.MONTHLY_COST: get_nested_config_value(
                        config, CONFIG_FIELDS.PRICING, CONFIG_FIELDS.PRICING_MONTHLY_TOTAL, default=0
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Config validation error for {customer_id}: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    async def get_customer_branding_css(self, customer_id: str) -> Dict[str, str]:
        """Get customer branding as CSS variables."""
        config = await self.get_customer_config(customer_id)
        
        branding = get_nested_config_value(config, CONFIG_FIELDS.BRANDING, default={})
        if not branding:
            return {}
        
        return get_branding_css_vars(branding)
    
    async def is_location_open_now(self, customer_id: str, location_id: str) -> bool:
        """Check if a specific location is currently open."""
        config = await self.get_customer_config(customer_id)
        
        if not config or "locations" not in config:
            return False
        
        # Find the location
        location = None
        for loc in config["locations"]:
            if loc.get("id") == location_id:
                location = loc
                break
        
        if not location or not location.get("isActive", True):
            return False
        
        # Check business hours
        business_hours = location.get("businessHours")
        if not business_hours:
            return True  # Assume open if no hours specified
        
        now = datetime.now()
        current_day = now.strftime("%A").lower()
        current_time = now.time()
        
        day_hours = business_hours.get(current_day)
        if not day_hours:
            return False  # Closed if no hours for today
        
        if day_hours.get("closed", False):
            return False
        
        try:
            open_time = time.fromisoformat(day_hours.get("open", "00:00"))
            close_time = time.fromisoformat(day_hours.get("close", "23:59"))
            
            return open_time <= current_time <= close_time
        except (ValueError, TypeError):
            return True  # Default to open if time parsing fails
    
    async def get_customer_compliance_frameworks(self, customer_id: str) -> List[str]:
        """Get compliance frameworks for customer."""
        config = await self.get_customer_config(customer_id)
        
        if not config or "compliance" not in config:
            return []
        
        return config["compliance"].get("frameworks", [])
    
    async def get_customer_locations_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get summary of customer locations."""
        config = await self.get_customer_config(customer_id)
        
        if not config or "locations" not in config:
            return {
                "total": 0,
                "active": 0,
                "open_now": 0,
                "locations": []
            }
        
        locations = config["locations"]
        active_count = 0
        open_now_count = 0
        
        for location in locations:
            if location.get("isActive", True):
                active_count += 1
                
                if await self.is_location_open_now(customer_id, location.get("id")):
                    open_now_count += 1
        
        return {
            "total": len(locations),
            "active": active_count,
            "open_now": open_now_count,
            "locations": [
                {
                    "id": loc.get("id"),
                    "name": loc.get("name"),
                    "isActive": loc.get("isActive", True),
                    "isOpenNow": await self.is_location_open_now(customer_id, loc.get("id"))
                }
                for loc in locations
            ]
        }
    
    async def reload_all_configs(self) -> None:
        """Reload all configurations from TypeScript files."""
        try:
            # Clear caches
            self._platform_config_cache = None
            self._customer_cache.clear()
            self.ts_bridge.clear_cache()
            
            # Reinitialize
            await self.initialize()
            
            logger.info("✅ All configurations reloaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Configuration reload failed: {e}")
            raise
    
    async def get_customer_pricing_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get customer pricing summary."""
        config = await self.get_customer_config(customer_id)
        
        if not config or "pricing" not in config:
            return {
                "monthlyTotal": 0,
                "baseCost": 0,
                "locationCost": 0,
                "locationCount": 0,
                "annualTotal": 0
            }
        
        pricing = config["pricing"]
        location_count = len(config.get("locations", []))
        monthly_total = pricing.get("monthlyTotal", 0)
        
        return {
            "monthlyTotal": monthly_total,
            "baseCost": pricing.get("baseCost", 0),
            "locationCost": pricing.get("locationCost", 0),
            "locationCount": location_count,
            "annualTotal": monthly_total * 12,
            "currency": "USD"
        }
    
    def is_initialized(self) -> bool:
        """Check if registry is initialized."""
        return self._initialized 