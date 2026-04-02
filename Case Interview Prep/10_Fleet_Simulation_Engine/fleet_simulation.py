"""
Fleet Simulation Engine - Skeleton Implementation

This module simulates a large fleet of batteries over time.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from enum import Enum
from random import Random
from dataclasses import dataclass


class BatteryStatus(Enum):
    """
    TODO: Define battery states
    Examples: IDLE, CHARGING, DISCHARGING, OFFLINE
    """
    pass


class SimulatedBattery:
    """
    Represents a single battery in the simulation.
    """
    
    def __init__(self, battery_id: str, capacity: float):
        """
        Initialize simulated battery.
        
        TODO:
        - Store battery_id, capacity
        - Set initial charge (e.g., random or 50% of capacity)
        - Set initial status (e.g., IDLE)
        - Track statistics: total_charged, total_discharged, offline_count
        """
        pass
    
    def charge(self, amount: float) -> None:
        """
        Charge the battery by amount.
        
        TODO:
        - Add amount to current_charge
        - Cap at capacity
        - Update total_charged statistic
        """
        pass
    
    def discharge(self, amount: float) -> None:
        """
        Discharge the battery by amount.
        
        TODO:
        - Subtract amount from current_charge
        - Don't go below 0
        - Update total_discharged statistic
        """
        pass
    
    def get_state(self) -> Dict:
        """
        TODO: Return battery state as dict
        """
        pass


class ControlPolicy(ABC):
    """
    Abstract control policy that decides what batteries should do.
    
    This is the Strategy pattern - different policies can be swapped in.
    """
    
    @abstractmethod
    def decide_action(self, battery: SimulatedBattery, 
                     step: int, random: Random) -> str:
        """
        Decide what action this battery should take at this step.
        
        TODO:
        - Return one of: "charge", "discharge", "idle", "offline", "online"
        - Logic depends on battery state and policy rules
        
        Args:
            battery: The battery to make decision for
            step: Current simulation step number
            random: Random number generator for stochastic decisions
            
        Returns:
            Action string
        """
        pass


class RandomPolicy(ControlPolicy):
    """
    Random control policy (for baseline testing).
    
    TODO: Each step, randomly choose an action
    - 40% idle
    - 25% charge
    - 25% discharge
    - 5% go offline
    - 5% come online (if offline)
    """
    
    def decide_action(self, battery: SimulatedBattery, 
                     step: int, random: Random) -> str:
        pass


class BalancedChargingPolicy(ControlPolicy):
    """
    Policy that tries to keep batteries at 50% charge.
    
    TODO: Logic:
    - If charge < 40%: charge
    - If charge > 60%: discharge
    - Otherwise: idle
    - Small random chance to go offline
    """
    
    def decide_action(self, battery: SimulatedBattery, 
                     step: int, random: Random) -> str:
        pass


class PeakShavingPolicy(ControlPolicy):
    """
    Policy that models peak shaving behavior.
    
    TODO: Logic:
    - During peak hours (step % 24 in [17,18,19,20]): discharge
    - During off-peak (step % 24 in [2,3,4,5]): charge
    - Otherwise: idle
    - Keep charge between 20% and 80%
    """
    
    def decide_action(self, battery: SimulatedBattery, 
                     step: int, random: Random) -> str:
        pass


@dataclass
class SimulationMetrics:
    """
    Aggregated metrics from simulation.
    
    TODO: Store:
    - total_steps_run
    - total_energy_charged
    - total_energy_discharged
    - average_charge_level
    - batteries_by_status: Dict[status, count]
    - total_offline_events
    """
    pass


class SimulationEngine:
    """
    Orchestrates fleet simulation.
    """
    
    def __init__(self, control_policy: ControlPolicy, 
                 num_batteries: int = 1000,
                 battery_capacity: float = 10.0,
                 random_seed: Optional[int] = None):
        """
        Initialize simulation engine.
        
        TODO:
        - Store control_policy
        - Create num_batteries SimulatedBattery instances
        - Initialize Random with seed (for reproducibility)
        - Initialize current_step to 0
        - Create metrics tracking
        """
        pass
    
    def step(self) -> None:
        """
        Advance simulation by one time step.
        
        TODO:
        - For each battery:
            - Ask control_policy what action to take
            - Execute the action:
                - "charge": battery.charge(charge_rate)
                - "discharge": battery.discharge(discharge_rate)
                - "idle": do nothing
                - "offline": set status to OFFLINE
                - "online": set status to IDLE
        - Increment current_step
        - Update metrics
        """
        pass
    
    def run(self, num_steps: int) -> SimulationMetrics:
        """
        Run simulation for multiple steps.
        
        TODO:
        - Call step() num_steps times
        - Optionally print progress every N steps
        - Collect final metrics
        - Return SimulationMetrics
        """
        pass
    
    def inject_fault(self, battery_id: str) -> None:
        """
        Inject a fault into a specific battery.
        
        TODO:
        - Find battery by ID
        - Set its status to OFFLINE
        - Log the fault injection
        """
        pass
    
    def inject_random_faults(self, probability: float = 0.01) -> int:
        """
        Randomly inject faults into batteries.
        
        TODO:
        - For each battery:
            - With given probability, call inject_fault()
        - Return count of faults injected
        """
        pass
    
    def get_fleet_summary(self) -> Dict:
        """
        Get current fleet state summary.
        
        TODO: Return:
        - total_batteries
        - batteries_by_status
        - average_charge_percent
        - total_capacity
        - total_current_charge
        - min_charge, max_charge
        """
        pass
    
    def get_battery_state(self, battery_id: str) -> Optional[Dict]:
        """
        Get state of a specific battery.
        
        TODO: Find battery and return its state
        """
        pass
    
    def change_policy(self, new_policy: ControlPolicy) -> None:
        """
        Switch to a different control policy mid-simulation.
        
        TODO:
        - Update self.control_policy
        - Log the policy change
        """
        pass


# Example usage and testing
if __name__ == "__main__":
    """
    TODO: Test your implementation
    
    Test scenarios:
    1. Create simulation with RandomPolicy and 100 batteries
    2. Run for 100 steps
    3. Check fleet summary after each 10 steps
    4. Inject random faults midway
    5. Switch to BalancedChargingPolicy
    6. Continue simulation for 100 more steps
    7. Compare metrics before and after policy change
    8. Test with PeakShavingPolicy
    9. Verify reproducibility with same random seed
    10. Scale test with 1000 batteries
    
    Visualization idea: Print simple ASCII chart of average charge over time
    """
    pass
