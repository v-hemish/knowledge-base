"""
Event-Driven Device Processor - Skeleton Implementation

This module processes device events using a dispatcher pattern.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class Event(ABC):
    """
    Base class for all device events.
    
    TODO:
    - Store common attributes: device_id, timestamp
    - Consider adding event_id for tracking
    """
    
    def __init__(self, device_id: str, timestamp: Optional[datetime] = None):
        """
        Initialize base event.
        
        TODO:
        - Store device_id
        - Store timestamp (use current time if not provided)
        """
        pass
    
    @abstractmethod
    def event_type(self) -> str:
        """
        Return the type identifier for this event.
        
        TODO: Each subclass should return its unique type string
        """
        pass


class BatteryOnlineEvent(Event):
    """Event fired when battery comes online."""
    
    def event_type(self) -> str:
        # TODO: Return "battery_online"
        pass


class BatteryOfflineEvent(Event):
    """Event fired when battery goes offline."""
    
    def event_type(self) -> str:
        # TODO: Return "battery_offline"
        pass


class ChargeStartedEvent(Event):
    """Event fired when battery begins charging."""
    
    def __init__(self, device_id: str, target_charge: Optional[float] = None, 
                 timestamp: Optional[datetime] = None):
        """
        TODO:
        - Call parent __init__
        - Store target_charge if provided
        """
        pass
    
    def event_type(self) -> str:
        # TODO: Return "charge_started"
        pass


class ChargeStoppedEvent(Event):
    """Event fired when battery stops charging."""
    
    def __init__(self, device_id: str, final_charge: Optional[float] = None,
                 timestamp: Optional[datetime] = None):
        """
        TODO:
        - Call parent __init__
        - Store final_charge if provided
        """
        pass
    
    def event_type(self) -> str:
        # TODO: Return "charge_stopped"
        pass


class FaultRaisedEvent(Event):
    """Event fired when battery reports a fault."""
    
    def __init__(self, device_id: str, fault_code: str, 
                 fault_message: Optional[str] = None,
                 timestamp: Optional[datetime] = None):
        """
        TODO:
        - Call parent __init__
        - Store fault_code and fault_message
        """
        pass
    
    def event_type(self) -> str:
        # TODO: Return "fault_raised"
        pass


class DeviceState:
    """
    Tracks the current state of a device.
    
    TODO: Decide what state to track:
    - Is device online?
    - Is it charging/discharging?
    - Current charge level?
    - Any active faults?
    """
    
    def __init__(self, device_id: str):
        """
        TODO: Initialize state tracking for a device
        """
        pass


class EventProcessor:
    """
    Processes device events and maintains device state.
    
    Strategy: Use a dispatcher pattern (dictionary mapping event types to handler methods)
    """
    
    def __init__(self):
        """
        Initialize the event processor.
        
        TODO:
        - Create a dictionary to store device states (key: device_id, value: DeviceState)
        - Create a dispatcher dict mapping event types to handler methods
          Example: {"battery_online": self._handle_battery_online, ...}
        - Initialize any tracking for invalid events
        """
        pass
    
    def process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Main entry point for processing an event.
        
        TODO:
        - Parse event_data to determine event type
        - Create the appropriate Event object
        - Look up the handler in the dispatcher
        - Call the handler
        - Return True if processed successfully, False otherwise
        - Log/count invalid events
        
        Args:
            event_data: Raw event data (e.g., from JSON)
            
        Returns:
            True if event was processed, False if invalid/ignored
        """
        pass
    
    def _parse_event(self, event_data: Dict[str, Any]) -> Optional[Event]:
        """
        Parse raw event data into an Event object.
        
        TODO:
        - Extract event_type from event_data
        - Extract device_id
        - Create and return the appropriate Event subclass
        - Return None if parsing fails
        - Handle missing fields gracefully
        
        Args:
            event_data: Raw event dictionary
            
        Returns:
            Parsed Event object or None if invalid
        """
        pass
    
    def _handle_battery_online(self, event: BatteryOnlineEvent) -> None:
        """
        Handle battery coming online.
        
        TODO:
        - Get or create DeviceState for this device
        - Update state to show device is online
        - Log the event
        """
        pass
    
    def _handle_battery_offline(self, event: BatteryOfflineEvent) -> None:
        """
        Handle battery going offline.
        
        TODO:
        - Get DeviceState for this device
        - Update state to show device is offline
        - If device was charging/discharging, stop that
        - Log the event
        """
        pass
    
    def _handle_charge_started(self, event: ChargeStartedEvent) -> None:
        """
        Handle charge started event.
        
        TODO:
        - Get DeviceState for this device
        - Verify device is online
        - Update state to show charging
        - Store target_charge if provided
        - Log the event
        """
        pass
    
    def _handle_charge_stopped(self, event: ChargeStoppedEvent) -> None:
        """
        Handle charge stopped event.
        
        TODO:
        - Get DeviceState for this device
        - Update state to show not charging
        - Update final charge level if provided
        - Log the event
        """
        pass
    
    def _handle_fault_raised(self, event: FaultRaisedEvent) -> None:
        """
        Handle fault event.
        
        TODO:
        - Get DeviceState for this device
        - Record the fault (code and message)
        - Possibly stop charging/discharging
        - Log the fault with high priority
        - Consider if device should go offline
        """
        pass
    
    def get_device_state(self, device_id: str) -> Optional[Dict]:
        """
        Get current state for a device.
        
        TODO:
        - Look up device in state dictionary
        - Return state info as dict
        - Return None if device not found
        """
        pass
    
    def get_all_devices(self) -> List[Dict]:
        """
        Get state for all devices.
        
        TODO: Return list of all device states
        """
        pass


# Example usage and testing
if __name__ == "__main__":
    """
    TODO: Test your implementation
    
    Test scenarios:
    1. Process BatteryOnline event
    2. Process ChargeStarted event
    3. Process ChargeStoppedEvent
    4. Process FaultRaised event
    5. Try processing invalid event data
    6. Try charging a battery that's offline
    7. Process events for multiple devices
    8. Verify state is tracked correctly
    """
    pass
