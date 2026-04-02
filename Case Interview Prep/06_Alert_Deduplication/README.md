# Alert Deduplication and Escalation

## Problem Statement

Build a service that receives alerts from multiple systems, deduplicates them, suppresses noise, and escalates when necessary.

## Requirements

Alert handling:
- **Group duplicate alerts**: Same alert from same source within time window
- **Suppress repeats**: Don't notify for duplicates within suppression window (e.g., 5 minutes)
- **Escalate after threshold**: If alert repeats N times, escalate to higher severity
- **Resolve incidents**: When recovery/clear event arrives, close the incident
- **Track incident lifecycle**: Created, acknowledged, escalated, resolved

## What This Tests

- Operational/SRE thinking
- Object modeling for alerts and incidents
- Time window management
- Incident lifecycle management
- Deduplication algorithms

## Key Design Questions

1. How do you define "duplicate" (same message? same source + error code?)
2. Should escalation be automatic or require manual trigger?
3. What happens to old resolved incidents?
4. How do you handle alert storms (thousands per second)?
5. Should alerts have severity levels from the start?

## Expected Classes

- `Alert` (individual alert)
- `Incident` (grouped alerts)
- `Severity` (Enum: INFO, WARNING, CRITICAL)
- `IncidentStatus` (Enum)
- `AlertProcessor` (main service)
- `DeduplicationKey` (defines what makes alerts "the same")

## Edge Cases to Consider

- Alert arrives after incident already resolved
- Recovery event with no matching incident
- Multiple sources generating same alert
- Time window boundaries
- Clock drift between systems

## Production Considerations

- Alert routing and notification channels
- On-call escalation integration
- Alert history retention
- Metrics: MTTA, MTTR, alert volume
- Integration with ticketing systems
- Silence/snooze functionality
