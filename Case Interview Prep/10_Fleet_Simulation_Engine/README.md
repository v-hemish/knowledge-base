# Fleet Simulation Engine

## Problem Statement

Build a simulation engine to model the behavior of 1,000 batteries over time.

## Requirements

Simulation behavior:
- At each time step, batteries can:
  - Start charging
  - Start discharging
  - Go offline
  - Come back online
  - Recover from faults

The engine must support:
- **Control policy abstraction**: Different strategies for deciding what each battery does
- **Simulation loop**: Advance time step by step
- **Summary metrics**: Aggregate statistics across the fleet
- **Fault injection**: Introduce random failures for testing

## What This Tests

- Strategy pattern (different control policies)
- System modeling and simulation design
- Extensibility to new policies
- Structured code organization
- Performance with many entities

## Key Design Questions

1. How do you model time (discrete steps vs continuous)?
2. Should battery behavior be deterministic or stochastic?
3. How do you make control policies pluggable?
4. What metrics are most valuable?
5. Should the simulation be reproducible (random seed)?

## Expected Classes

- `Battery` (simulated battery)
- `ControlPolicy` (abstract strategy)
- Concrete policies: `RandomPolicy`, `BalancedChargingPolicy`, etc.
- `SimulationEngine` (orchestrator)
- `SimulationMetrics` (statistics collector)
- `SimulationConfig` (parameters)

## Edge Cases to Consider

- All batteries offline simultaneously
- Infinite charging (battery never stops)
- Negative charge due to bugs
- Time step size too small/large
- No control policy set

## Production Considerations

- Visualization of simulation results
- Configurable time scale
- Save/load simulation state
- Parallel simulation runs
- Integration with real telemetry data
- What-if scenario modeling
