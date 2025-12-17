import os
import time
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FileLock:
    """
    A simple cross-process file lock using file existence.
    """
    def __init__(self, lock_file: str, timeout: int = 60, retry_interval: float = 0.5):
        self.lock_file = lock_file
        self.timeout = timeout
        self.retry_interval = retry_interval
        
    def acquire(self) -> bool:
        """Acquire the lock. Returns True if successful, False if timed out."""
        start_time = time.time()
        while True:
            try:
                # Exclusive creation - fails if file exists
                with open(self.lock_file, "x") as f:
                    f.write(f"Locked at {datetime.now().isoformat()}")
                return True
            except FileExistsError:
                # Check for stale lock
                if self._is_stale():
                    logger.warning(f"Removing stale lock file: {self.lock_file}")
                    self._release()
                    continue
                
                # Wait and retry
                time.sleep(self.retry_interval)
                if time.time() - start_time > self.timeout:
                    logger.error(f"Timeout waiting for lock: {self.lock_file}")
                    return False
            except Exception as e:
                logger.error(f"Error acquiring lock: {e}")
                return False

    def release(self):
        """Release the lock."""
        self._release()

    def _release(self):
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")

    def _is_stale(self) -> bool:
        """Check if the lock file is too old (stale)."""
        if not os.path.exists(self.lock_file):
            return False
        try:
            mtime = os.path.getmtime(self.lock_file)
            return (time.time() - mtime) > self.timeout
        except OSError:
            return False

@contextmanager
def file_lock(lock_path: str, timeout: int = 60):
    """Context manager for file locking."""
    lock = FileLock(lock_path, timeout=timeout)
    acquired = lock.acquire()
    try:
        if acquired:
            yield True
        else:
            raise TimeoutError(f"Could not acquire lock on {lock_path}")
    finally:
        if acquired:
            lock.release()
