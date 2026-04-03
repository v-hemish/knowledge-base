# Event-Driven Device Processor

## Problem Statement

Build a processor that handles various device events in an extensible, type-safe way.

## Requirements

Events to handle:
- `BatteryOnline`: Battery comes online
- `BatteryOffline`: Battery goes offline
- `ChargeStarted`: Battery begins charging
- `ChargeStopped`: Battery stops charging
- `FaultRaised`: Battery reports a fault

The processor must:
- Parse incoming events (could be JSON, dict, or objects)
- Route events to appropriate handlers
- Update system state based on events
- Ignore or log invalid/malformed events
- Be easily extensible to new event types

## What This Tests

- Polymorphism and inheritance
- Factory or dispatcher pattern
- Robustness to bad input
- Separation of concerns
- Clean, extensible architecture

## Key Design Questions

1. Should you use inheritance (base `Event` class) or a simpler approach?
2. How do you route events to handlers? (if/elif, dictionary dispatch, visitor pattern?)
3. Where should validation happen?
4. How do you make it easy to add new event types?
5. What state does the processor maintain?

## Expected Classes

- `Event` (base class or protocol)
- Concrete event classes: `BatteryOnlineEvent`, `BatteryOfflineEvent`, etc.
- `EventProcessor` (coordinator)
- Optional: `EventHandler` interface or handler functions

## Edge Cases to Consider

- Malformed event data
- Unknown event types
- Events for non-existent devices
- Duplicate events
- Events arriving out of order

## Production Considerations

- Event persistence/replay
- Dead letter queue for failed events
- Idempotency
- Event versioning
- Monitoring and alerting


Will do this tomorrow. 