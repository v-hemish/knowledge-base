# Inventory System for Install Operations

## Problem Statement

Model an inventory system for battery installation teams who need to track parts across warehouses and vans.

## Requirements

Entities:
- **Warehouse**: Central storage location
- **Van**: Mobile storage for installation teams
- **Part**: Individual component (e.g., battery, inverter, mounting bracket)
- **Transfer Request**: Moving parts between locations
- **Install Order**: Parts needed for an installation

Operations:
- **Reserve parts**: Allocate parts for an install order
- **Move parts**: Transfer between warehouse and van, or between vans
- **Prevent negative stock**: Reject transfers that would make stock negative
- **Log all inventory actions**: Full audit trail

## What This Tests

- Domain modeling (real-world business logic)
- Invariant enforcement (stock >= 0)
- Transaction-like operations
- Entity relationships
- OOP structure for business domains

## Key Design Questions

1. Should warehouse and van share a common `Location` interface?
2. How do you enforce stock constraints?
3. What happens if you try to reserve unavailable parts?
4. Should transfers be atomic (all-or-nothing)?
5. How do you model different part types?

## Expected Classes

- `Part` (or `PartType` and `PartInstance`)
- `Location` (base class)
- `Warehouse` (extends Location)
- `Van` (extends Location)
- `StockLevel` (tracks quantity at location)
- `TransferRequest`
- `InstallOrder`
- `InventoryManager` (orchestrator)

## Edge Cases to Consider

- Transferring more parts than available
- Concurrent reservations for same parts
- Cancelled install orders (unreserve parts)
- Lost/damaged parts
- Van returns parts to warehouse

## Production Considerations

- Database transactions
- Real-time stock visibility
- Reorder points and procurement
- Part expiration/warranty tracking
- Location-based routing optimization
- Integration with ERP systems
