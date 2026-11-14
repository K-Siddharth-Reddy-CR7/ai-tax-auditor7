import json
import os
import sys

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(EXP))
BACKEND = os.path.join(REPO, "backend")
DATA = os.path.join(EXP, "data")
GEN = os.path.join(DATA, "generated")
RESULTS = os.path.join(EXP, "results")
FIGURES = os.path.join(EXP, "figures")
PILOT = os.path.join(EXP, "pilot")

if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def config():
    with open(os.path.join(EXP, "config.json"), encoding="utf-8") as fh:
        return json.load(fh)
