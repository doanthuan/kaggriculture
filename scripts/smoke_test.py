"""Run one local game against Kaggle's built-in random agent."""

from kaggle_environments import make


def main() -> None:
    env = make("kaggriculture", debug=True)
    env.run(["main.py", "random"])
    for player, state in enumerate(env.steps[-1]):
        print(f"Player {player}: status={state.status}, reward={state.reward}")
    if any(state.status != "DONE" for state in env.steps[-1]):
        raise SystemExit("Local game did not finish successfully")


if __name__ == "__main__":
    main()
