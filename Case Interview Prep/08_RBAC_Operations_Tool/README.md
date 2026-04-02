# RBAC for Internal Operations Tool

## Problem Statement

Design role-based access control (RBAC) for an internal platform that manages infrastructure.

## Requirements

Roles:
- **Admin**: Full access to everything
- **Operator**: Can view and send commands, cannot change config
- **Engineer**: Can view, send commands, update config, cannot acknowledge alerts
- **Viewer**: Read-only access

Actions:
- `view_status`: See system status
- `send_command`: Send commands to devices
- `update_config`: Modify system configuration
- `acknowledge_alert`: Acknowledge and resolve alerts

The system must:
- Check permissions before allowing actions
- Make it easy to add new roles and actions
- Provide audit logging for all access checks
- Support role assignment to users

## What This Tests

- Security mindset
- Policy design patterns
- OOP and extensibility
- Clean authorization abstractions
- Audit and compliance thinking

## Key Design Questions

1. Should you use role-based, permission-based, or both?
2. How do you model "admin has all permissions"?
3. Should roles be hierarchical (engineer inherits operator)?
4. How do you make adding new actions/roles easy?
5. What should audit logs include?

## Expected Classes

- `Role` (Enum or class)
- `Action` (Enum)
- `User` (has roles)
- `PermissionChecker` or `AuthorizationService`
- `AuditLog` (tracks access attempts)

## Edge Cases to Consider

- User with multiple roles
- Action that doesn't exist
- User with no roles
- Permission check for null user
- Role assignment to non-existent user

## Production Considerations

- Integration with identity provider (OAuth, LDAP)
- Role hierarchy and inheritance
- Temporary permission elevation
- Resource-level permissions (not just action-level)
- Permission caching
- Compliance reporting
