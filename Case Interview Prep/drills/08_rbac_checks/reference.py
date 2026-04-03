"""
Drill 8 — Reference + concepts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

Action = str  # "read" | "write" | "deploy"

_ROLE_PERMS: Dict[str, Set[Action]] = {
    "admin": {"read", "write", "deploy"},
    "operator": {"read", "write"},
    "viewer": {"read"},
}


@dataclass
class AuthzService:
    _audit: List[Tuple[str, Action, str]] = field(default_factory=list)

    def audit_log(self) -> List[Tuple[str, Action, str]]:
        return list(self._audit)

    def is_allowed(self, username: str, roles: Set[str], action: Action) -> bool:
        allowed_actions: Set[Action] = set()
        for r in roles:
            allowed_actions |= _ROLE_PERMS.get(r, set())
        ok = action in allowed_actions
        self._audit.append((username, action, "allowed" if ok else "denied"))
        return ok


# --- Concepts: AuthzService.is_allowed ---
# - Union of role permissions models **multiple roles** without nested if/else trees.
# - Unknown roles contribute nothing (`get(r, set())`)—say aloud whether fail-closed is desired.
# - Audit tuples are minimal; production logs add request id, resource, timestamp, reason code.
# - Next step up: **ABAC** (row-level) or **OPA**/Rego when policies explode.


if __name__ == "__main__":
    s = AuthzService()
    assert s.is_allowed("u", {"admin"}, "deploy")
    print("reference ok")
