"""
Drill 8 — RBAC checks + audit log (25 min)
Search for "FILL" below. Run: python practice.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Set, Tuple


Action = Literal["read", "write", "deploy"]


@dataclass
class AuthzService:
    """
    Roles:
      admin: read, write, deploy
      operator: read, write
      viewer: read
    A user may have multiple roles; union permissions.
    Each check appends one audit row: (username, action, "allowed"|"denied").
    """

    _audit: List[Tuple[str, Action, str]] = field(default_factory=list)

    def audit_log(self) -> List[Tuple[str, Action, str]]:
        return list(self._audit)

    def is_allowed(self, username: str, roles: Set[str], action: Action) -> bool:
        # --- FILL: AuthzService.is_allowed ---
        # WHERE: body of this method.
        # WHAT: Union permissions from all roles: admin -> {read,write,deploy}; operator -> {read,write};
        #       viewer -> {read}. Unknown role name contributes no permissions.
        #       ok = action in that union. Append (username, action, "allowed"|"denied") to self._audit.
        #       Return ok. (Define a module-level dict ROLE -> set of actions, or equivalent.)
        raise NotImplementedError


if __name__ == "__main__":
    s = AuthzService()
    assert s.is_allowed("ada", {"viewer"}, "read") is True
    assert s.is_allowed("ada", {"viewer"}, "write") is False
    assert s.is_allowed("bob", {"operator"}, "deploy") is False
    assert s.is_allowed("carl", {"admin"}, "deploy") is True
    assert s.is_allowed("dora", {"viewer", "operator"}, "write") is True
    log = s.audit_log()
    assert log[0] == ("ada", "read", "allowed")
    assert log[1] == ("ada", "write", "denied")
    print("ok")
