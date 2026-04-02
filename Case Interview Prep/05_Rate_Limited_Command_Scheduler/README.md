# Rate-Limited Command Scheduler

## Problem Statement

Build a scheduler that sends commands to devices while respecting rate limits at both device and global levels.

## Requirements

Constraints:
- **Per-device limit**: Maximum 1 command per device every 10 seconds
- **Global limit**: Maximum 100 commands per minute across all devices
- **Retry policy**: Retry failed commands up to 3 times

The scheduler must:
- Accept command requests
- Queue commands if limits are exceeded
- Automatically send commands when limits allow
- Retry failed commands with backoff
- Track command status (pending, sent, succeeded, failed)

## What This Tests

- Queue design and management
- Time-based rate limiting algorithms
- Retry logic with backoff
- Practical backend reasoning
- Handling concurrent constraints

## Key Design Questions

1. How do you track rate limits (sliding window, fixed window, token bucket)?
2. Should the scheduler run in background or be explicitly triggered?
3. How do you prioritize commands (FIFO, priority queue)?
4. What happens to failed commands after max retries?
5. How do you prevent starvation when global limit is hit?

## Expected Classes

- `Command` (represents a command to send)
- `CommandStatus` (Enum)
- `RateLimiter` (tracks and enforces limits)
- `CommandScheduler` (main orchestrator)
- `DeviceRateLimiter` (per-device tracking)

## Edge Cases to Consider

- Commands for same device queued rapidly
- Global limit reached across all devices
- Commands timing out
- System pause/resume
- Clock skew or time going backwards

## Production Considerations

- Persistent queue (survive restarts)
- Distributed rate limiting (Redis)
- Priority levels for urgent commands
- Metrics: queue depth, command latency, success rate
- Dead letter queue for permanently failed commands
- Backpressure signaling to clients
