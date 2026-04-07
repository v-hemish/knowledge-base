"""
Game 2 solution: Potion Crafting (6 micro-drills)

Theory covered:
- collection operations on dict/list
- all/any style predicates
- two-phase safe mutation
- deterministic output for testability
"""

from __future__ import annotations


def missing_count(backpack: dict[str, int], recipe: dict[str, int]) -> int:
    """Micro 1: compute total unit shortfall."""
    total = 0
    for ing, needed in recipe.items():
        total += max(0, needed - backpack.get(ing, 0))
    return total


def is_craftable(backpack: dict[str, int], recipe: dict[str, int]) -> bool:
    """Micro 2: craftability predicate."""
    return missing_count(backpack, recipe) == 0


def craftable_potions(backpack: dict[str, int], recipes: dict[str, dict[str, int]]) -> list[str]:
    """Micro 3: collect craftable names sorted."""
    return sorted(name for name, rec in recipes.items() if is_craftable(backpack, rec))


def consume_ingredients(backpack: dict[str, int], recipe: dict[str, int]) -> None:
    """Micro 4: safe consume with validation first."""
    for ing, needed in recipe.items():
        if backpack.get(ing, 0) < needed:
            raise ValueError(f"not enough {ing}")

    for ing, needed in recipe.items():
        backpack[ing] -= needed
        if backpack[ing] == 0:
            del backpack[ing]


def low_stock(backpack: dict[str, int], threshold: int) -> list[str]:
    """Micro 5: return sorted low-stock ingredient names."""
    return sorted([ing for ing, count in backpack.items() if count <= threshold])


def scarcity_score(backpack: dict[str, int], recipe: dict[str, int]) -> float:
    """Micro 6: simple ratio-based scarcity score."""
    return sum(needed / max(backpack.get(ing, 0), 1) for ing, needed in recipe.items())


if __name__ == "__main__":
    bag = {"herb": 3, "water": 2}
    consume_ingredients(bag, {"herb": 1, "water": 2})
    assert bag == {"herb": 2}
    print("solution ok")
