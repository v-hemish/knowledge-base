# Deployment Manager for dev/stage/prod

## Problem Statement

Model different deployment environments (dev, staging, production) with different rules and constraints.

## Requirements

Each environment has:
- **Allowed deploy times**: Time windows when deployments are permitted
- **Approval requirement**: Whether manual approval is needed
- **Rollback policy**: Automatic vs manual rollback
- **Health checks**: Validation after deployment

The deployment manager must:
- Validate whether a deploy is allowed at current time
- Simulate a deployment process
- Execute health checks
- Rollback on failure according to environment policy
- Prevent deployments during blackout windows

## What This Tests

- OOP modeling of business rules
- Environment-specific logic
- Separation of concerns
- Platform/infrastructure thinking
- Policy enforcement

## Key Design Questions

1. Should each environment be a separate class or use composition?
2. How do you model time-based rules?
3. What does a "deployment" object look like?
4. How do you simulate success/failure?
5. Should rollback be automatic or require explicit triggers?

## Expected Classes

- `Environment` (base class or protocol)
- `DevEnvironment`, `StagingEnvironment`, `ProductionEnvironment`
- `DeploymentManager`
- `Deployment` (represents a deployment attempt)
- `HealthCheck` interface or class

## Edge Cases to Consider

- Deployment during blackout window
- Missing approval for production
- Failed health checks
- Multiple deployments to same environment
- Rollback failures

## Production Considerations

- Integration with CI/CD
- Deployment artifact versioning
- Blue-green or canary deployments
- Deployment history and audit logs
- Notifications and alerting
- Deployment locks to prevent concurrent deploys
