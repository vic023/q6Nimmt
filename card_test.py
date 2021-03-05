from game_objs import *
import random

def main():
    pile = Pile(0, [randomCard() for _ in range(5)])
    print(repr(pile))
    pile.sort()
    print(repr(pile))
    random.shuffle(pile.list)
    print(repr(pile))
    print(pile)

if __name__ == '__main__':
    main()
