"""Bulkhead pattern implementation for fault isolation"""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

class BulkheadExecutor:
    """Isolate different service components using separate thread pools"""
    
    def __init__(self):
        self.payment_pool = ThreadPoolExecutor(
            max_workers=10, 
            thread_name_prefix="payment"
        )
        self.booking_pool = ThreadPoolExecutor(
            max_workers=20, 
            thread_name_prefix="booking"
        )
        self.notification_pool = ThreadPoolExecutor(
            max_workers=5, 
            thread_name_prefix="notify"
        )
        self.iot_pool = ThreadPoolExecutor(
            max_workers=8, 
            thread_name_prefix="iot"
        )
    
    def execute_payment(self, task: Callable, *args, **kwargs):
        """Execute payment task in isolated thread pool"""
        try:
            return self.payment_pool.submit(task, *args, **kwargs)
        except Exception as e:
            logger.error(f"Payment bulkhead error: {e}")
            raise
    
    def execute_booking(self, task: Callable, *args, **kwargs):
        """Execute booking task in isolated thread pool"""
        try:
            return self.booking_pool.submit(task, *args, **kwargs)
        except Exception as e:
            logger.error(f"Booking bulkhead error: {e}")
            raise
    
    def execute_notification(self, task: Callable, *args, **kwargs):
        """Execute notification task in isolated thread pool"""
        try:
            return self.notification_pool.submit(task, *args, **kwargs)
        except Exception as e:
            logger.error(f"Notification bulkhead error: {e}")
            raise
    
    def execute_iot(self, task: Callable, *args, **kwargs):
        """Execute IoT task in isolated thread pool"""
        try:
            return self.iot_pool.submit(task, *args, **kwargs)
        except Exception as e:
            logger.error(f"IoT bulkhead error: {e}")
            raise
    
    def shutdown(self):
        """Gracefully shutdown all thread pools"""
        self.payment_pool.shutdown(wait=True)
        self.booking_pool.shutdown(wait=True)
        self.notification_pool.shutdown(wait=True)
        self.iot_pool.shutdown(wait=True)

bulkhead_executor = BulkheadExecutor()