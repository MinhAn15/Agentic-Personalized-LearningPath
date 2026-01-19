import asyncio
import asyncpg
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    dsn = os.getenv("DATABASE_URL")
    logger.info(f"Testing connection to: {dsn}")
    
    try:
        conn = await asyncpg.connect(dsn)
        logger.info("✅ Connection successful!")
        await conn.close()
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        # Try finding detailed info
        import socket
        try:
            host = dsn.split("@")[1].split(":")[0]
            ip = socket.gethostbyname(host)
            logger.info(f"Resolved {host} to {ip}")
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            res = s.connect_ex((host, 5432))
            logger.info(f"Socket connect_ex to {host}:5432 returned {res} (0=Success)")
            s.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_connection())
