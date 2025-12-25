from ..integration.airi_bridge import airi_status


def run() -> None:
    print("AIRI (bridge)")
    print(airi_status())
