from abc import ABC, abstractmethod
import time
import random

class BaseChannelAdapter(ABC):
    def __init__(self, channel):
        self.channel = channel

    @abstractmethod
    def update_inventory(self, room_type, start_date, end_date, availability_dict):
        pass

class MockOTAAdapter(BaseChannelAdapter):
    def update_inventory(self, room_type, start_date, end_date, availability_dict):
        # Simulate network delay
        time.sleep(0.5)
        # 10% chance of failure to test retry/logging
        if random.random() < 0.1:
            raise Exception("Mock OTA API Timeout or Error")
        return True
