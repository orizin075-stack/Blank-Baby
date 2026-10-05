"""v941 flat dependency adapter. Original archive SHA is listed in provenance."""
from pathlib import Path
def activate():
    return Path(__file__).resolve().parent.parent
