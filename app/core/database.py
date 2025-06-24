import hashlib
import logging
from typing import Dict, Optional, AsyncGenerator, Any
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import asyncpg
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .config import settings, get_customer_config, CustomerConfig

logger = logging.getLogger(__name__)

# Base class for all Data Vault 2.0 models
Base = declarative_base()

class DatabaseManager:
    """Multi-customer database connection manager"""
    
    def __init__(self):
        self._engines: Dict[str, Any] = {}
        self._sessions: Dict[str, Any] = {}
        self._async_engines: Dict[str, Any] = {}
        self._async_sessions: Dict[str, Any] = {}
        
        # System database (for platform operations)
        self._system_engine = None
        self._system_session = None
        
    def get_system_engine(self):
        """Get system database engine for platform operations"""
        if not self._system_engine:
            self._system_engine = create_engine(
                settings.database.DEFAULT_DATABASE_URL,
                pool_size=settings.database.DB_POOL_SIZE,
                max_overflow=settings.database.DB_MAX_OVERFLOW,
                pool_timeout=settings.database.DB_POOL_TIMEOUT,
                echo=settings.DEBUG
            )
        return self._system_engine
    
    def get_system_session(self) -> Session:
        """Get system database session"""
        if not self._system_session:
            engine = self.get_system_engine()
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self._system_session = SessionLocal
        return self._system_session()
    
    def get_customer_engine(self, customer_id: str):
        """Get database engine for specific customer"""
        if customer_id not in self._engines:
            try:
                customer_config = get_customer_config(customer_id)
                database_url = customer_config.database_url
                
                if not database_url:
                    raise ValueError(f"No database URL configured for customer: {customer_id}")
                
                self._engines[customer_id] = create_engine(
                    database_url,
                    pool_size=settings.database.DB_POOL_SIZE,
                    max_overflow=settings.database.DB_MAX_OVERFLOW,
                    pool_timeout=settings.database.DB_POOL_TIMEOUT,
                    echo=settings.DEBUG
                )
                
                logger.info(f"Created database engine for customer: {customer_id}")
                
            except Exception as e:
                logger.error(f"Failed to create engine for customer {customer_id}: {e}")
                raise
        
        return self._engines[customer_id]
    
    def get_customer_session(self, customer_id: str) -> Session:
        """Get database session for specific customer"""
        if customer_id not in self._sessions:
            engine = self.get_customer_engine(customer_id)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self._sessions[customer_id] = SessionLocal
        
        return self._sessions[customer_id]()
    
    async def get_customer_async_engine(self, customer_id: str):
        """Get async database engine for specific customer"""
        if customer_id not in self._async_engines:
            try:
                customer_config = get_customer_config(customer_id)
                database_url = customer_config.database_url
                
                if not database_url:
                    raise ValueError(f"No database URL configured for customer: {customer_id}")
                
                # Convert sync URL to async URL
                async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
                
                self._async_engines[customer_id] = create_async_engine(
                    async_url,
                    pool_size=settings.database.DB_POOL_SIZE,
                    max_overflow=settings.database.DB_MAX_OVERFLOW,
                    echo=settings.DEBUG
                )
                
                logger.info(f"Created async database engine for customer: {customer_id}")
                
            except Exception as e:
                logger.error(f"Failed to create async engine for customer {customer_id}: {e}")
                raise
        
        return self._async_engines[customer_id]
    
    async def get_customer_async_session(self, customer_id: str) -> AsyncSession:
        """Get async database session for specific customer"""
        if customer_id not in self._async_sessions:
            engine = await self.get_customer_async_engine(customer_id)
            AsyncSessionLocal = async_sessionmaker(
                engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            self._async_sessions[customer_id] = AsyncSessionLocal
        
        return self._async_sessions[customer_id]()
    
    async def validate_customer_database(self, customer_id: str) -> Dict[str, Any]:
        """Validate customer database has proper Data Vault 2.0 structure"""
        try:
            engine = self.get_customer_engine(customer_id)
            
            with engine.connect() as conn:
                # Check for required schemas
                required_schemas = ['auth', 'business', 'audit', 'util', 'ref']
                schema_check = conn.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = ANY(:schemas)
                """), {"schemas": required_schemas})
                
                existing_schemas = [row[0] for row in schema_check]
                missing_schemas = set(required_schemas) - set(existing_schemas)
                
                # Check for core Data Vault tables
                table_check = conn.execute(text("""
                    SELECT table_schema, table_name 
                    FROM information_schema.tables 
                    WHERE table_schema IN ('auth', 'business', 'audit')
                    AND table_type = 'BASE TABLE'
                """))
                
                existing_tables = [(row[0], row[1]) for row in table_check]
                
                # Check for Data Vault 2.0 patterns
                hub_tables = [t for t in existing_tables if t[1].endswith('_h')]
                satellite_tables = [t for t in existing_tables if t[1].endswith('_s')]
                link_tables = [t for t in existing_tables if t[1].endswith('_l')]
                
                validation_result = {
                    "customer_id": customer_id,
                    "database_valid": len(missing_schemas) == 0,
                    "existing_schemas": existing_schemas,
                    "missing_schemas": list(missing_schemas),
                    "data_vault_structure": {
                        "hub_tables": len(hub_tables),
                        "satellite_tables": len(satellite_tables),
                        "link_tables": len(link_tables),
                        "total_tables": len(existing_tables)
                    },
                    "validation_timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Database validation completed for customer: {customer_id}")
                return validation_result
                
        except Exception as e:
            logger.error(f"Database validation failed for customer {customer_id}: {e}")
            return {
                "customer_id": customer_id,
                "database_valid": False,
                "error": str(e),
                "validation_timestamp": datetime.now(timezone.utc).isoformat()
            }

class DataVaultUtils:
    """Data Vault 2.0 utility functions"""
    
    @staticmethod
    def hash_binary(*args) -> bytes:
        """Generate SHA-256 hash for Data Vault hash keys"""
        combined = "|".join(str(arg) for arg in args)
        return hashlib.sha256(combined.encode()).digest()
    
    @staticmethod
    def hash_diff(*args) -> bytes:
        """Generate hash diff for satellite change detection"""
        combined = "|".join(str(arg) for arg in args if arg is not None)
        return hashlib.sha256(combined.encode()).digest()
    
    @staticmethod
    def current_load_date() -> datetime:
        """Get current load date in UTC"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def get_record_source() -> str:
        """Get record source identifier"""
        return settings.database.RECORD_SOURCE_SYSTEM

class DatabaseRouter:
    """Routes database operations to correct customer database"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    @asynccontextmanager
    async def get_session(self, customer_id: str) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
        session = await self.db_manager.get_customer_async_session(customer_id)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    def get_sync_session(self, customer_id: str) -> Session:
        """Get synchronous database session"""
        return self.db_manager.get_customer_session(customer_id)
    
    async def execute_raw_sql(self, customer_id: str, sql: str, params: Optional[Dict] = None) -> Any:
        """Execute raw SQL against customer database"""
        async with self.get_session(customer_id) as session:
            result = await session.execute(text(sql), params or {})
            return result

# Global database manager instance
db_manager = DatabaseManager()

# Global database router instance
db_router = DatabaseRouter(db_manager)

# Dependency for FastAPI
async def get_customer_db_session(customer_id: str) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for customer database sessions"""
    async with db_router.get_session(customer_id) as session:
        yield session

def get_sync_customer_db_session(customer_id: str) -> Session:
    """Synchronous version for non-async code"""
    return db_router.get_sync_session(customer_id)

# Utility functions for Data Vault 2.0 operations
def create_tenant_hub_record(
    tenant_bk: str, 
    record_source: str = None
) -> Dict[str, Any]:
    """Create a tenant hub record following Data Vault 2.0 patterns"""
    if not record_source:
        record_source = DataVaultUtils.get_record_source()
    
    tenant_hk = DataVaultUtils.hash_binary(tenant_bk)
    
    return {
        "tenant_hk": tenant_hk,
        "tenant_bk": tenant_bk,
        "load_date": DataVaultUtils.current_load_date(),
        "record_source": record_source
    }

def create_user_hub_record(
    user_bk: str,
    tenant_hk: bytes,
    record_source: str = None
) -> Dict[str, Any]:
    """Create a user hub record following Data Vault 2.0 patterns"""
    if not record_source:
        record_source = DataVaultUtils.get_record_source()
    
    user_hk = DataVaultUtils.hash_binary(user_bk, tenant_hk.hex())
    
    return {
        "user_hk": user_hk,
        "user_bk": user_bk,
        "tenant_hk": tenant_hk,
        "load_date": DataVaultUtils.current_load_date(),
        "record_source": record_source
    }

async def validate_database_connectivity() -> Dict[str, Any]:
    """Validate connectivity to all configured customer databases"""
    validation_results = []
    
    # Validate system database
    try:
        system_session = db_manager.get_system_session()
        system_session.execute(text("SELECT 1"))
        system_session.close()
        
        validation_results.append({
            "database": "system",
            "status": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        validation_results.append({
            "database": "system",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "overall_status": "healthy" if all(r["status"] == "connected" for r in validation_results) else "unhealthy",
        "databases": validation_results,
        "validation_timestamp": datetime.now(timezone.utc).isoformat()
    } 