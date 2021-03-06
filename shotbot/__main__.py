import sys

from .client import ShotBot


def main(args):
    """
    Usage: python -m shotbot "<first name> <last name>"
    """
    shotbot = ShotBot()
    if len(args) == 1:
        shotbot.start()
    elif len(args) == 2:
        shotbot.generate(args[1])
    elif len(args) == 3:
        shotbot.generate(args[1], args[2])

if __name__ == "__main__":
    main(sys.argv)