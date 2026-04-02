# Circuit Breaker for External API

## Problem Statement

Implement a circuit breaker pattern to protect your system from cascading failures when calling an unreliable external service.

## Requirements

The circuit breaker has three states:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Too many failures, requests are blocked immediately
- **HALF_OPEN**: Testing if service recovered, limited requests allowed

Behavior:
- Track consecutive failures
- Open circuit after failure threshold (e.g., 5 failures)
- Block all requests while open
- After cooldown period (e.g., 60 seconds), transition to half-open
- In half-open, allow 1 test request
- If test succeeds, close circuit
- If test fails, reopen circuit

## What This Tests

- State machine design
- Resilience patterns (critical for infrastructure)
- Clean abstractions
- Failure handling and recovery
- Time-based logic

## Key Design Questions

1. How do you track time for cooldown periods?
2. Should the circuit breaker execute the call or just wrap it?
3. How do you define "failure" (exception, timeout, status code)?
4. Should you track success rate or just consecutive failures?
5. What metrics should you expose?

## Expected Classes

- `CircuitBreakerState` (Enum)
- `CircuitBreaker` (main class)
- Optional: `CircuitBreakerConfig` for thresholds

## Edge Cases to Consider

- Rapid consecutive calls
- Time synchronization issues
- Transient vs permanent failures
- Thread safety (if concurrent)
- Manual reset/override

## Production Considerations

- Metrics and monitoring (open/close events)
- Configurable thresholds per service
- Gradual recovery (more than 1 test request)
- Distributed circuit breaker (shared state)
- Half-open timeout
