# Python Interview Game Drills (30 x 5 min)

This pack is tuned for a technical screen focused on code literacy and real-world coding, not LeetCode tricks.

Format:
- 5 game worlds
- 6 micro-drills per world
- 30 total drills
- each micro-drill: ~5 minutes

Main goals:
- practice clear assumptions
- write clean, elegant Python
- model small real-world behaviors with readable code

## How to use

1. Open `drills/NN_.../README.md` for prompt + interview signal.
2. In each `practice.py`, solve one `FILL` block at a time.
3. If stuck, open `solution.py` for a complete answer plus theory-heavy docstrings.
4. Run each drill with `python3 practice.py`.
5. Narrate assumptions out loud as if in a live interview.

## Game Worlds (5 x 6 micro-drills)

| # | Folder | Game theme | Core concepts covered |
|---|--------|------------|------------------|
| 1 | `drills/01_space_cargo` | Spaceship logistics | parsing, validation, dataclass, invariants, idempotency, formatting |
| 2 | `drills/02_potion_crafting` | Crafting system | dict/list/set ops, counting, filtering, two-phase mutation, ranking |
| 3 | `drills/03_maze_messenger` | Navigation service | grid parsing, neighbors, BFS, shortest path, queue usage |
| 4 | `drills/04_boss_retry_arena` | Reliability engine | exception design, retry policy, backoff, fail-fast behavior |
| 5 | `drills/05_tournament_scoreboard` | Match backend | class design, aggregation, sorting tie-breakers, report generation |

## Optional verifier

Run:

`python3 drills/verify_against_solution.py`

This temporarily swaps your `practice.py` functions with `solution.py` and confirms tests in each practice file pass.
