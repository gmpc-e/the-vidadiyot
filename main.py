"""The Vidadiyot — entry point.

Init pygame via Game, push the starting state, run the loop. Nothing else
belongs here.
"""
from game.core.game import Game
from game.core.menu_state import MenuState


def main():
    game = Game()
    game.push(MenuState(game))
    game.audio.start_music()
    game.run()


if __name__ == "__main__":
    main()
