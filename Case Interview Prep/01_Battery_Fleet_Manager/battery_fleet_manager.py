"""
Battery Fleet Manager - Skeleton Implementation

This module manages a fleet of home batteries with state management and command handling.
"""

from enum import Enum
from typing import Dict, List, Optional


class BatteryStatus(Enum):
    """
    Enum representing possible battery states.
    
    TODO: Define the four battery states mentioned in the requirements.
    Think about: What transitions are valid between these states?
    """
    pass  # Define: CHARGING, DISCHARGING, IDLE, OFFLINE

    CHARGING = "CHARGING"
    DISCHARGING = "DISCHARGING"
    IDLE = "IDLE"
    OFFLINE = "OFFLINE"

class Battery:
    """
    Represents a single battery with its properties and state.
    
    Responsibilities:
    - Store battery attributes (id, capacity, charge, status)
    - Validate state transitions
    - Update charge level
    - Enforce invariants (charge <= capacity, charge >= 0)
    """
    
    def __init__(self, battery_id: str, capacity: float, initial_charge: float = 0.0):
        """
        Initialize a new battery.
        
        TODO:
        - Store battery_id, capacity, initial_charge
        - Set initial status (probably IDLE or OFFLINE)
        - Validate that initial_charge <= capacity
        - Validate that capacity and initial_charge are non-negative
        
        Args:
            battery_id: Unique identifier for the battery
            capacity: Total storage capacity in kWh
            initial_charge: Starting charge level in kWh (default 0.0)
        
        Raises:
            ValueError: If validation fails
        """
        self.battery_id = battery_id
        self.capacity = capacity
        self.current_charge = initial_charge
        
        self.initial_charge = initial_charge
        self.status = BatteryStatus.IDLE 
        
        if initial_charge > capacity:
            raise ValueError("Charge > 0, not possible")
        if initial_charge < 0:
            raise ValueError("Charge < 0, not possible")
        
        if capacity < 0:
            raise ValueError("Capacity < 0, not possible")
        
    
    def can_transition_to(self, new_status: BatteryStatus) -> bool:
        """
        Check if transition from current status to new status is valid.
        
        TODO: Define valid transitions. Examples:
        - OFFLINE can only go to IDLE
        - IDLE can go to CHARGING, DISCHARGING, or OFFLINE
        - CHARGING can go to IDLE or OFFLINE
        - Cannot go directly from CHARGING to DISCHARGING
        
        Args:
            new_status: The desired new status
            
        Returns:
            True if transition is valid, False otherwise
        """
        if self.status == new_status:
            return True
        if self.status == BatteryStatus.OFFLINE and new_status == BatteryStatus.IDLE: 
            return True
        if self.status == BatteryStatus.IDLE and new_status in [BatteryStatus.CHARGING, BatteryStatus.DISCHARGING, BatteryStatus.OFFLINE]:
            return True
        if self.status == BatteryStatus.CHARGING and new_status in [BatteryStatus.IDLE, BatteryStatus.OFFLINE]:
            return True
        if self.status == BatteryStatus.DISCHARGING and new_status in [BatteryStatus.IDLE, BatteryStatus.OFFLINE]:
            return True
        return False
    
    def update_status(self, new_status: BatteryStatus) -> None:
        """
        Update the battery status if transition is valid.
        
        TODO:
        - Check if transition is valid using can_transition_to()
        - If valid, update self.status
        - If invalid, raise an exception with clear error message
        
        Args:
            new_status: The new status to transition to
            
        Raises:
            ValueError: If transition is not allowed
        """
        if self.can_transition_to(new_status):
            self.status = new_status
        else: 
            raise ValueError("Invalid transition")
    
    def update_charge(self, new_charge: float) -> None:
        """
        Update the current charge level.
        
        TODO:
        - Validate that new_charge is between 0 and capacity
        - Update self.current_charge
        - Raise exception if out of bounds
        
        Args:
            new_charge: New charge level in kWh
            
        Raises:
            ValueError: If charge is invalid
        """
        if 0 <= new_charge <= self.capacity:
            self.current_charge = new_charge
        else: 
            raise ValueError("Charge out of bounds")
        
    
    def get_info(self) -> Dict:
        """
        Return battery information as a dictionary.
        
        TODO: Return dict with id, capacity, current_charge, status
        """
        return {
            "id": self.battery_id,
            "capacity": self.capacity, 
            "current_charge": self.current_charge,
            "status": self.status.value,
            "initial_charge": self.initial_charge
        }


class FleetManager:
    """
    Manages a fleet of batteries.
    
    Responsibilities:
    - Register new batteries
    - Route commands to specific batteries
    - Provide fleet-wide statistics
    - Coordinate battery operations
    """
    
    def __init__(self):
        """
        Initialize the fleet manager.
        
        TODO:
        - Create an empty dictionary to store batteries (key: battery_id, value: Battery)
        """
        self.batteries = {}
    
    def register_battery(self, battery: Battery) -> None:
        """
        Add a new battery to the fleet.
        
        TODO:
        - Check if battery_id already exists
        - If exists, raise exception (or decide on different behavior)
        - Add battery to the internal dictionary
        
        Args:
            battery: The Battery instance to register
            
        Raises:
            ValueError: If battery with same ID already exists
        """
        if battery.battery_id in self.batteries: 
            raise ValueError("Battery with Same ID already present")
        self.batteries[battery.battery_id] = battery
    
    
    def get_battery(self, battery_id: str) -> Optional[Battery]:
        """
        Retrieve a battery by ID.
        
        TODO: Return the battery if it exists, None otherwise
        
        Args:
            battery_id: The ID of the battery to retrieve
            
        Returns:
            The Battery instance or None if not found
        """
        if battery_id in self.batteries:
            return self.batteries[battery_id]
        return None
    
    def send_command(self, battery_id: str, command: str) -> None:
        """
        Send a command to a specific battery.
        
        Commands: "charge", "discharge", "stop"
        
        TODO:
        - Get the battery by ID
        - If not found, raise exception
        - Map command to appropriate status:
            - "charge" -> BatteryStatus.CHARGING
            - "discharge" -> BatteryStatus.DISCHARGING
            - "stop" -> BatteryStatus.IDLE
        - Call battery.update_status() with the new status
        - Handle any exceptions from invalid transitions
        
        Args:
            battery_id: The ID of the target battery
            command: The command to execute ("charge", "discharge", "stop")
            
        Raises:
            ValueError: If battery not found or command invalid
        """
        battery = self.get_battery(battery_id)
        
        m = {
            "charge": BatteryStatus.CHARGING,
            "discharge": BatteryStatus.DISCHARGING,
            "stop": BatteryStatus.IDLE
        }
        if battery is None: 
            raise ValueError("Battery not found")
        
        if command not in m:
            raise ValueError("Invalid command")
        
        battery.update_status(m[command])
        

    def get_fleet_summary(self) -> Dict:
        """
        Return aggregate statistics for the entire fleet.
        
        TODO: Calculate and return:
        - total_batteries: Total number of batteries
        - total_capacity: Sum of all battery capacities
        - total_charge: Sum of all current charges
        - average_charge_percent: Average charge level across fleet
        - batteries_by_status: Count of batteries in each status
        - online_batteries: Count of batteries not in OFFLINE state
        
        Returns:
            Dictionary with fleet statistics
        """
        total_batteries = len(self.batteries)
        total_capacity, total_charge, online_batteries = 0, 0, 0
        batteries_summary = {
            "OFFLINE": 0, 
            "IDLE":0, 
            "CHARGING":0,
            "DISCHARGING":0
        }
        for battery_id, battery in self.batteries.items(): 
            total_capacity += self.batteries[battery_id].capacity
            total_charge += self.batteries[battery_id].current_charge 
            if battery.status != BatteryStatus.OFFLINE: 
                online_batteries +=1 
            batteries_summary[battery.status.value] += 1
        average_charge_percent = (total_charge / total_capacity) * 100 if total_capacity > 0 else 0.0
        
        return {
        
        "total_batteries":total_batteries, 
        "total_capacity":total_capacity, 
        "total_charge": total_charge,
        "average_charge_percent":average_charge_percent,
        "batteries_by_status":batteries_summary,
        "online_batteries":online_batteries

        }
	
    
    def list_batteries(self) -> List[Dict]:
        """
        Return information about all batteries in the fleet.
        
        TODO:
        - Iterate through all batteries
        - Collect their info using battery.get_info()
        - Return as a list
        
        Returns:
            List of battery information dictionaries
        """
        
        list_of_batteries = list()
        for battery_id, battery in self.batteries.items(): 
            battery_info = battery.get_info()
            list_of_batteries.append(battery_info)	
        return list_of_batteries

# Example usage and testing
def run_tests():
    print("Running tests...")

    # -----------------------------
    # 1. Battery initialization
    # -----------------------------
    b1 = Battery("bat1", 10.0, 5.0)
    assert b1.battery_id == "bat1"
    assert b1.capacity == 10.0
    assert b1.current_charge == 5.0
    assert b1.status == BatteryStatus.IDLE

    # -----------------------------
    # 2. Invalid battery creation
    # -----------------------------
    try:
        Battery("bad1", 10.0, 15.0)
        assert False, "Expected ValueError when initial_charge > capacity"
    except ValueError:
        pass

    try:
        Battery("bad2", 10.0, -1.0)
        assert False, "Expected ValueError for negative initial charge"
    except ValueError:
        pass

    try:
        Battery("bad3", -5.0, 0.0)
        assert False, "Expected ValueError for negative capacity"
    except ValueError:
        pass

    # -----------------------------
    # 3. Valid status transitions
    # -----------------------------
    b2 = Battery("bat2", 20.0, 10.0)

    b2.update_status(BatteryStatus.CHARGING)
    assert b2.status == BatteryStatus.CHARGING

    b2.update_status(BatteryStatus.IDLE)
    assert b2.status == BatteryStatus.IDLE

    b2.update_status(BatteryStatus.DISCHARGING)
    assert b2.status == BatteryStatus.DISCHARGING

    b2.update_status(BatteryStatus.IDLE)
    assert b2.status == BatteryStatus.IDLE

    b2.update_status(BatteryStatus.OFFLINE)
    assert b2.status == BatteryStatus.OFFLINE

    b2.update_status(BatteryStatus.IDLE)
    assert b2.status == BatteryStatus.IDLE

    # -----------------------------
    # 4. Invalid status transition
    # -----------------------------
    b3 = Battery("bat3", 15.0, 5.0)
    b3.update_status(BatteryStatus.CHARGING)

    try:
        b3.update_status(BatteryStatus.DISCHARGING)
        assert False, "Expected ValueError for CHARGING -> DISCHARGING"
    except ValueError:
        pass

    # -----------------------------
    # 5. Charge updates
    # -----------------------------
    b4 = Battery("bat4", 12.0, 6.0)
    b4.update_charge(8.0)
    assert b4.current_charge == 8.0

    try:
        b4.update_charge(20.0)
        assert False, "Expected ValueError for charge above capacity"
    except ValueError:
        pass

    try:
        b4.update_charge(-1.0)
        assert False, "Expected ValueError for negative charge"
    except ValueError:
        pass

    # -----------------------------
    # 6. Fleet registration
    # -----------------------------
    fleet = FleetManager()
    fleet.register_battery(b1)
    fleet.register_battery(b2)

    assert fleet.get_battery("bat1") == b1
    assert fleet.get_battery("missing") is None

    try:
        fleet.register_battery(b1)
        assert False, "Expected ValueError for duplicate battery ID"
    except ValueError:
        pass

    # -----------------------------
    # 7. Fleet commands
    # -----------------------------
    fleet.send_command("bat1", "charge")
    assert fleet.get_battery("bat1").status == BatteryStatus.CHARGING

    fleet.send_command("bat1", "stop")
    assert fleet.get_battery("bat1").status == BatteryStatus.IDLE

    fleet.send_command("bat1", "discharge")
    assert fleet.get_battery("bat1").status == BatteryStatus.DISCHARGING

    try:
        fleet.send_command("bat1", "invalid")
        assert False, "Expected ValueError for invalid command"
    except ValueError:
        pass

    try:
        fleet.send_command("unknown", "charge")
        assert False, "Expected ValueError for unknown battery"
    except ValueError:
        pass

    # -----------------------------
    # 8. Offline battery behavior
    # -----------------------------
    b5 = Battery("bat5", 10.0, 3.0)
    b5.update_status(BatteryStatus.OFFLINE)

    try:
        b5.update_status(BatteryStatus.CHARGING)
        assert False, "Expected ValueError for OFFLINE -> CHARGING"
    except ValueError:
        pass

    # -----------------------------
    # 9. Fleet summary
    # -----------------------------
    fleet2 = FleetManager()
    a = Battery("a", 10.0, 5.0)   # 50%
    c = Battery("c", 20.0, 10.0)  # 50%
    d = Battery("d", 30.0, 15.0)  # 50%

    c.update_status(BatteryStatus.CHARGING)
    d.update_status(BatteryStatus.OFFLINE)

    fleet2.register_battery(a)
    fleet2.register_battery(c)
    fleet2.register_battery(d)

    summary = fleet2.get_fleet_summary()

    assert summary["total_batteries"] == 3
    assert summary["total_capacity"] == 60.0
    assert summary["total_charge"] == 30.0
    assert summary["average_charge_percent"] == 50.0
    assert summary["online_batteries"] == 2
    assert summary["batteries_by_status"]["IDLE"] == 1
    assert summary["batteries_by_status"]["CHARGING"] == 1
    assert summary["batteries_by_status"]["OFFLINE"] == 1
    assert summary["batteries_by_status"]["DISCHARGING"] == 0

    # -----------------------------
    # 10. List batteries
    # -----------------------------
    battery_list = fleet2.list_batteries()
    assert len(battery_list) == 3
    assert all("id" in item for item in battery_list)
    assert all("status" in item for item in battery_list)

    print("All tests passed!")


if __name__ == "__main__":
    run_tests()