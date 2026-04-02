# Job Runner With Dependencies

## Problem Statement

Implement an internal job runner that executes jobs in the correct order based on their dependencies.

## Requirements

Each job has:
- `job_id`: unique identifier
- `dependencies`: list of job_ids that must complete first
- Can succeed, fail, or retry

The runner must:
- Execute jobs in valid order (respecting dependencies)
- Detect circular dependencies before execution
- Block downstream jobs if upstream job fails
- Support retry logic for failed jobs
- Return final execution report with all job results

## What This Tests

- Dependency graph algorithms (topological sort)
- Orchestration logic
- Clean API design
- Error propagation
- Graph cycle detection

## Key Design Questions

1. How do you detect circular dependencies? (DFS, topological sort?)
2. Should failed jobs block all downstream jobs or just direct dependents?
3. Can jobs run in parallel if dependencies allow?
4. What information should the execution report include?
5. Should retries be automatic or manual?

## Expected Classes

- `JobStatus` (Enum)
- `Job` (represents a job)
- `JobResult` (execution outcome)
- `JobRunner` (orchestrator)
- `DependencyGraph` (optional helper for validation)

## Edge Cases to Consider

- Circular dependencies (A depends on B depends on A)
- Self-dependency (A depends on A)
- Jobs with no dependencies
- Jobs depending on non-existent jobs
- Empty job list

## Production Considerations

- Persistent job queue (database)
- Distributed execution (workers)
- Job timeout handling
- Partial retry (retry only failed jobs in a workflow)
- Job artifacts and logs
- Scheduling (cron-like)
- Priority levels
