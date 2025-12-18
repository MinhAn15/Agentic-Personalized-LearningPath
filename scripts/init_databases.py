"""
Database Initialization Script

Usage:
    python scripts/init_databases.py

This script:
1. Tests connection to all databases
2. Initializes Neo4j schema (constraints, indexes)
3. Verifies Redis is working
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.database_factory import initialize_databases, shutdown_databases, get_factory
from backend.database.neo4j_schema import Neo4jSchemaManager
from backend.config import get_settings


async def test_connections():
    """Test all database connections"""
    print("\n" + "=" * 50)
    print("🔌 Testing Database Connections")
    print("=" * 50)
    
    success = await initialize_databases()
    
    if success:
        print("\n✅ All databases connected successfully!")
        
        # Health check
        factory = get_factory()
        health = await factory.health_check()
        print(f"\n📊 Health Check: {health}")
        
        return True
    else:
        print("\n❌ Database connection failed!")
        return False


async def init_neo4j_schema():
    """Initialize Neo4j schema"""
    print("\n" + "=" * 50)
    print("📐 Initializing Neo4j Schema")
    print("=" * 50)
    
    factory = get_factory()
    
    if factory.neo4j:
        schema_manager = Neo4jSchemaManager(factory.neo4j)
        await schema_manager.initialize_schema()
        print("✅ Neo4j schema initialized!")
    else:
        print("⚠️ Neo4j not connected, skipping schema initialization")


async def test_redis():
    """Test Redis operations"""
    print("\n" + "=" * 50)
    print("🧪 Testing Redis Operations")
    print("=" * 50)
    
    factory = get_factory()
    
    if factory.redis:
        # Test set/get
        await factory.redis.set("test_key", "test_value", ttl=60)
        value = await factory.redis.get("test_key")
        
        if value == "test_value":
            print("✅ Redis set/get working!")
        else:
            print(f"⚠️ Redis test failed: expected 'test_value', got '{value}'")
            
        # Cleanup
        await factory.redis.delete("test_key")
    else:
        print("⚠️ Redis not connected, skipping test")


async def main():
    """Run all initialization steps"""
    settings = get_settings()
    
    print("\n" + "=" * 50)
    print("🚀 Agentic Learning Path - Database Initialization")
    print("=" * 50)
    print(f"\nConfiguration:")
    print(f"  Neo4j URI: {settings.NEO4J_URI}")
    print(f"  Redis URL: {settings.REDIS_URL}")
    
    try:
        # Step 1: Test connections
        if not await test_connections():
            print("\n❌ Aborting: Could not connect to databases")
            print("\n💡 Make sure Docker is running:")
            print("   docker-compose up -d neo4j redis postgres chroma")
            return
        
        # Step 2: Initialize Neo4j schema
        await init_neo4j_schema()
        
        # Step 3: Test Redis
        await test_redis()
        
        print("\n" + "=" * 50)
        print("✅ All database initialization complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await shutdown_databases()


if __name__ == "__main__":
    asyncio.run(main())
