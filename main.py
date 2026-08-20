"""The Vidadiyot — entry point.

Init pygame via Game, push the starting state, run the loop. Nothing else
belongs here.

    ./venv/bin/python main.py            # the game
    ./venv/bin/python main.py --boss     # straight into the Emri duel
"""
import argparse

from game.core.game import Game
from game.core.menu_state import MenuState


def main():
    ap = argparse.ArgumentParser(description="The Vidadiyot")
    # ⚠️ A test hatch, and deliberately a *flag* rather than a menu entry. The
    # duel is the end of a full run; putting it on the title screen would let a
    # player skip the level to reach it, which is the one thing it must not be.
    ap.add_argument("--boss", action="store_true",
                    help="skip the level and start the Emri duel (for testing)")
    ap.add_argument("--warrior", choices=("wallad", "roni"),
                    help="who to play as; only meaningful with --boss")
    args = ap.parse_args()

    game = Game()
    if args.warrior:
        game.warrior = args.warrior
    if args.boss:
        from game.core.play_state import PlayState
        game.push(PlayState(game, duel=True))
    else:
        game.push(MenuState(game))
    # music now belongs to whichever state is on screen (MenuState starts it)
    game.run()


if __name__ == "__main__":
    main()
