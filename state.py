"""Shared mutable game state.

Always access these as `state.player`, `state.world`, etc. (via `import state`).
Doing `from state import player` would copy the value once and go stale
when a level reloads.

Why a separate file? Many files (soldier, projectiles, objects, ui...) all need
to know the current player, world and scroll amount. Keeping them here avoids
circular imports and means there is one single source of truth.
"""

screen_scroll = 0       # how many pixels the world shifted THIS frame (set by the player's move())
background_scroll = 0   # total distance scrolled so far (used for the parallax background and level end)
world = None            # the current World object (tiles + obstacle list)
player = None           # the current player Soldier
health_bar = None       # the player's HealthBar