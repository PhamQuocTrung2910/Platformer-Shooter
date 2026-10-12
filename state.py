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
player = None           # the current Player
health_bar = None       # the player's HealthBar
background_theme = 'forest'   # which background set to draw (set by world.load_level)
# Level exit requirement (reset by world.load_level)
kills = {}              # enemy type -> how many the player has killed this level
kills_required = {}     # enemy type -> how many must be killed to unlock the exit
exit_blocked_until = 0  # time (ms) until which the kill counter flashes after touching a locked exit


def quota_met():
    """True when every enemy type has reached its required kill count."""
    return all(kills.get(kind, 0) >= need for kind, need in kills_required.items())