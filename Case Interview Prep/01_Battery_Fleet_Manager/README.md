# Battery Fleet Manager

## Problem Statement

Design a system to manage a fleet of home batteries.

## Requirements

Each battery has:
- `id` (unique identifier)
- `capacity` (total storage capacity in kWh)
- `current_charge` (current charge level in kWh)
- `status`: one of `charging`, `discharging`, `idle`, `offline`

The system must support:
- **Register battery**: Add a new battery to the fleet
- **Update battery status**: Change battery state (charging/discharging/idle/offline)
- **Send commands**: Instruct battery to charge/discharge/stop
- **Reject invalid transitions**: Prevent impossible state changes (e.g., charging while offline)
- **Return fleet summary**: Aggregate statistics across all batteries

## What This Tests

- Class design and encapsulation
- Enum usage for states
- State transition validation
- Invariant enforcement (e.g., charge can't exceed capacity)
- Clean API design

## Key Design Questions

1. Should `Battery` be responsible for validating its own state transitions?
2. How do you model valid state transitions?
3. What happens if you try to charge an offline battery?
4. Should the fleet manager have any control policies?
5. What metrics should the fleet summary include?

## Expected Classes

- `BatteryStatus` (Enum)
- `Battery` (Entity)
- `FleetManager` (Coordinator)

## Edge Cases to Consider

- Battery charge exceeds capacity
- Invalid state transitions (offline -> charging)
- Duplicate battery IDs
- Negative charge values
- Commands to non-existent batteries

## Production Considerations

- Persistent storage (database)
- Concurrent access (thread-safety)
- Event logging for audit trail
- Metrics and monitoring
- Battery health degradation over time
