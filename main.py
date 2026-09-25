"""Minimal Kaggriculture submission entry point.

Replace this valid PASS policy with a farming strategy before competing.
"""


def agent(obs: dict) -> dict:
    """Return one action for the farmer and no market orders."""
    return {"farmer": ["PASS"], "hands": [], "market": []}
