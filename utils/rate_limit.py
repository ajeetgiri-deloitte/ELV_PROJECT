# utils/rate_limit.py
from django.core.cache import cache
from datetime import datetime, timedelta
import hashlib

class FileUploadRateLimiter:
    def __init__(self, request, max_uploads=10, time_window_minutes=5):
        self.request = request
        self.max_uploads = max_uploads
        self.time_window = time_window_minutes * 60  # Convert to seconds
        
    def get_session_key(self):
        """Generate a unique key for the session"""
        user_id = self.request.session.get('bulk_user_id')
        if user_id:
            return f"file_upload_rate_{user_id}"
        
        # Fallback to IP-based if no user session
        ip = self.get_client_ip()
        return f"file_upload_rate_ip_{ip}"
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def check_and_record(self, file_count=1):
        """
        Check if upload is allowed and record it
        Returns: (is_allowed, remaining_uploads, wait_time)
        """
        cache_key = self.get_session_key()
        
        # Get current upload records
        upload_records = cache.get(cache_key, [])
        
        # Clean old records
        current_time = datetime.now()
        upload_records = [t for t in upload_records 
                         if (current_time - t).total_seconds() < self.time_window]
        
        # Check limit
        if len(upload_records) + file_count > self.max_uploads:
            # Calculate wait time
            if upload_records:
                oldest_record = min(upload_records)
                wait_seconds = self.time_window - (current_time - oldest_record).total_seconds()
                wait_minutes = int(wait_seconds / 60) + 1
                return False, self.max_uploads - len(upload_records), wait_minutes
            return False, self.max_uploads - len(upload_records), self.time_window // 60
        
        # Record new uploads
        for _ in range(file_count):
            upload_records.append(current_time)
        
        # Store in cache (expire after time window)
        cache.set(cache_key, upload_records, self.time_window)
        
        remaining = self.max_uploads - len(upload_records)
        return True, remaining, 0
    
    def reset(self):
        """Reset rate limit for current session/IP"""
        cache_key = self.get_session_key()
        cache.delete(cache_key)