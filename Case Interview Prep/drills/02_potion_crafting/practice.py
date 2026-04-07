"""Game 2 practice: 6 micro-drills (5 min each)."""

from __future__ import annotations


def missing_count(backpack: dict[str, int], recipe: dict[str, int]) -> int:
    """Micro 1: total missing units to craft one recipe."""
    # --- FILL 1 ---
    raise NotImplementedError


def is_craftable(backpack: dict[str, int], recipe: dict[str, int]) -> bool:
    """Micro 2: check craftability."""
    # --- FILL 2 ---
    raise NotImplementedError


def craftable_potions(backpack: dict[str, int], recipes: dict[str, dict[str, int]]) -> list[str]:
    """Micro 3: list craftable recipe names sorted."""
    # --- FILL 3 ---
    raise NotImplementedError


def consume_ingredients(backpack: dict[str, int], recipe: dict[str, int]) -> None:
    """Micro 4: two-phase mutation."""
    # --- FILL 4 ---
    raise NotImplementedError


def low_stock(backpack: dict[str, int], threshold: int) -> list[str]:
    """Micro 5: ingredient names with count <= threshold, sorted."""
    # --- FILL 5 ---
    raise NotImplementedError


def scarcity_score(backpack: dict[str, int], recipe: dict[str, int]) -> float:
    """Micro 6: sum(required / max(owned,1)) across ingredients."""
    # --- FILL 6 ---
    raise NotImplementedError


if __name__ == "__main__":
    bag = {"herb": 5, "water": 2, "crystal": 1}
    recipes = {
        "heal_small": {"herb": 2, "water": 1},
        "heal_big": {"herb": 4, "water": 2},
        "mana": {"crystal": 2, "water": 1},
    }

    assert missing_count(bag, recipes["heal_small"]) == 0
    assert missing_count(bag, recipes["mana"]) == 1
    assert is_craftable(bag, recipes["heal_big"]) is True
    assert is_craftable(bag, recipes["mana"]) is False
    assert craftable_potions(bag, recipes) == ["heal_big", "heal_small"]

    consume_ingredients(bag, recipes["heal_small"])
    assert bag == {"herb": 3, "water": 1, "crystal": 1}

    try:
        consume_ingredients(bag, recipes["mana"])
        assert False, "should fail because crystal is missing"
    except ValueError:
        pass

    assert low_stock(bag, 1) == ["crystal", "water"]
    assert round(scarcity_score({"herb": 2}, {"herb": 4, "water": 1}), 2) == 3.0

    print("ok")
