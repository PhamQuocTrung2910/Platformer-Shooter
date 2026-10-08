"""Shared mutable game state.

Always access these as `state.player`, `state.world`, etc. (via `import state`).
Doing `from state import player` would copy the value once and go stale
when a level reloads.
"""

screen_scroll = 0
background_scroll = 0
world = None
player = None
health_bar = None