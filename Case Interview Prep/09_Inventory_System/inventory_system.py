"""
Inventory System for Install Operations - Skeleton Implementation

This module manages parts inventory across warehouses and vans.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class LocationType(Enum):
    """
    TODO: Define location types
    Examples: WAREHOUSE, VAN
    """
    pass


class TransferStatus(Enum):
    """
    TODO: Define transfer statuses
    Examples: PENDING, IN_TRANSIT, COMPLETED, CANCELLED
    """
    pass


@dataclass
class Part:
    """
    Represents a type of part in inventory.
    
    TODO: Store:
    - part_id: unique identifier
    - name: part name
    - sku: stock keeping unit
    - description: optional description
    """
    pass


class Location(ABC):
    """
    Base class for inventory locations.
    
    Both warehouses and vans are locations that hold parts.
    """
    
    def __init__(self, location_id: str, name: str, location_type: LocationType):
        """
        TODO:
        - Store location_id, name, location_type
        - Create dict to track stock levels (key: part_id, value: quantity)
        """
        pass
    
    @abstractmethod
    def get_capacity(self) -> Optional[int]:
        """
        Get maximum capacity for this location.
        
        TODO:
        - Warehouse: return None (unlimited)
        - Van: return max items (e.g., 50)
        """
        pass
    
    def get_stock(self, part_id: str) -> int:
        """
        Get current stock level for a part.
        
        TODO: Return quantity, or 0 if part not stocked
        """
        pass
    
    def add_stock(self, part_id: str, quantity: int) -> None:
        """
        Add quantity of a part to this location.
        
        TODO:
        - Validate quantity > 0
        - Check capacity if applicable
        - Add to existing stock or create new entry
        """
        pass
    
    def remove_stock(self, part_id: str, quantity: int) -> None:
        """
        Remove quantity of a part from this location.
        
        TODO:
        - Validate quantity > 0
        - Check that current stock >= quantity
        - If not enough stock, raise InsufficientStockError
        - Subtract from stock
        
        Raises:
            InsufficientStockError: If not enough stock available
        """
        pass
    
    def get_total_items(self) -> int:
        """
        Get total number of items at this location.
        
        TODO: Sum quantities across all parts
        """
        pass


class Warehouse(Location):
    """
    Warehouse location with (effectively) unlimited capacity.
    """
    
    def __init__(self, location_id: str, name: str):
        """
        TODO: Call parent __init__ with LocationType.WAREHOUSE
        """
        pass
    
    def get_capacity(self) -> Optional[int]:
        """
        TODO: Return None (unlimited capacity)
        """
        pass


class Van(Location):
    """
    Van location with limited capacity.
    """
    
    def __init__(self, location_id: str, name: str, max_capacity: int = 50):
        """
        TODO:
        - Call parent __init__ with LocationType.VAN
        - Store max_capacity
        """
        pass
    
    def get_capacity(self) -> Optional[int]:
        """
        TODO: Return max_capacity
        """
        pass


@dataclass
class TransferRequest:
    """
    Represents a request to move parts between locations.
    
    TODO: Store:
    - transfer_id
    - from_location_id
    - to_location_id
    - part_id
    - quantity
    - status
    - requested_at
    - completed_at
    """
    pass


@dataclass
class InstallOrder:
    """
    Represents parts needed for an installation.
    
    TODO: Store:
    - order_id
    - parts_needed: Dict[part_id, quantity]
    - assigned_van_id: which van has the parts
    - reserved: whether parts are reserved
    """
    pass


class InventoryManager:
    """
    Manages inventory operations across all locations.
    """
    
    def __init__(self):
        """
        Initialize inventory manager.
        
        TODO:
        - Create dict for locations (key: location_id)
        - Create dict for parts catalog (key: part_id)
        - Create list for transfer requests
        - Create list for install orders
        - Initialize audit log
        """
        pass
    
    def register_location(self, location: Location) -> None:
        """
        Register a warehouse or van.
        
        TODO: Add location to locations dict
        """
        pass
    
    def register_part(self, part: Part) -> None:
        """
        Register a part type in the catalog.
        
        TODO: Add part to parts dict
        """
        pass
    
    def add_initial_stock(self, location_id: str, part_id: str, quantity: int) -> None:
        """
        Add initial stock to a location.
        
        TODO:
        - Get location
        - Call location.add_stock()
        - Log the action
        """
        pass
    
    def reserve_parts_for_order(self, order: InstallOrder, van_id: str) -> bool:
        """
        Reserve parts from warehouse for an install order.
        
        TODO:
        - For each part in order.parts_needed:
            - Check if warehouse has sufficient stock
        - If all parts available:
            - Mark order as reserved
            - Associate with van_id
            - Return True
        - If any part insufficient:
            - Don't reserve anything (atomic operation)
            - Return False
        
        Note: This doesn't move parts yet, just reserves them
        """
        pass
    
    def transfer_parts(self, from_location_id: str, to_location_id: str,
                      part_id: str, quantity: int) -> TransferRequest:
        """
        Transfer parts between locations.
        
        TODO:
        - Get from_location and to_location
        - Create TransferRequest with PENDING status
        - Validate from_location has enough stock
        - If to_location is Van, check capacity
        - Remove stock from from_location
        - Add stock to to_location
        - Update transfer status to COMPLETED
        - Log the transfer
        - Return TransferRequest
        
        Raises:
            InsufficientStockError: If source lacks stock
            CapacityExceededError: If destination can't fit
        """
        pass
    
    def get_location_inventory(self, location_id: str) -> Dict[str, int]:
        """
        Get all parts and quantities at a location.
        
        TODO:
        - Get location
        - Return its stock levels as dict {part_id: quantity}
        """
        pass
    
    def get_total_stock(self, part_id: str) -> Dict[str, int]:
        """
        Get stock levels for a part across all locations.
        
        TODO:
        - Iterate all locations
        - Get stock of part_id at each
        - Return dict {location_id: quantity}
        """
        pass
    
    def get_audit_log(self) -> List[Dict]:
        """
        Get full audit trail of inventory operations.
        
        TODO:
        - Return list of all logged actions
        - Include: timestamp, action type, location, part, quantity
        """
        pass


class InsufficientStockError(Exception):
    """Raised when trying to use more stock than available."""
    pass


class CapacityExceededError(Exception):
    """Raised when trying to add more items than location can hold."""
    pass


# Example usage and testing
if __name__ == "__main__":
    """
    TODO: Test your implementation
    
    Test scenarios:
    1. Register warehouse and vans
    2. Add parts catalog
    3. Add stock to warehouse
    4. Create install order
    5. Reserve parts for order
    6. Transfer parts from warehouse to van
    7. Try to transfer more than available -> should fail
    8. Try to overfill van capacity -> should fail
    9. Check inventory at different locations
    10. Review audit log
    """
    pass
