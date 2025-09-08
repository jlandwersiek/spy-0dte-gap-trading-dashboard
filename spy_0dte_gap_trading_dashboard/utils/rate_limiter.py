"""Yahoo Finance rate limiter"""
import time

class YahooRateLimiter:
    """Rate limiter for Yahoo Finance to prevent API abuse"""
    
    def __init__(self):
        self.last_request = {}
        self.min_interval = 1.5
        self.request_count = 0
        self.session_start = time.time()
        self.max_requests_per_hour = 100
    
    def can_make_request(self, symbol: str) -> bool:
        """Check if we can make a request for this symbol"""
        current_time = time.time()
        
        if self.request_count >= self.max_requests_per_hour:
            if (current_time - self.session_start) < 3600:
                return False
            else:
                self.request_count = 0
                self.session_start = current_time
        
        if symbol in self.last_request:
            time_since_last = current_time - self.last_request[symbol]
            if time_since_last < self.min_interval:
                return False
        
        return True
    
    def wait_if_needed(self, symbol: str):
        """Wait if needed to respect rate limits"""
        if not self.can_make_request(symbol):
            time.sleep(self.min_interval)
    
    def record_request(self, symbol: str):
        """Record that we made a request"""
        self.last_request[symbol] = time.time()
        self.request_count += 1
