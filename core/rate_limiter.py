import time
from collections import defaultdict
from typing import Tuple
from app.config import settings

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.limit = settings.API_RATE_LIMIT
        self.period = 60  # seconds
    
    def is_rate_limited(self, client_id: str) -> Tuple[bool, int]:
        """Check if client is rate limited"""
        current_time = time.time()
        client_requests = self.requests[client_id]
        
        # Remove old requests
        client_requests = [t for t in client_requests if current_time - t < self.period]
        self.requests[client_id] = client_requests
        
        if len(client_requests) >= self.limit:
            wait_time = int(self.period - (current_time - client_requests[0]))
            return True, max(0, wait_time)
        
        # Add current request
        client_requests.append(current_time)
        return False, 0