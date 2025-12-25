from .airi_client import AiriClient


def airi_status() -> str:
    c = AiriClient()
    s = c.status()
    p = c.decide("bridge_status")
    return f"- {s.output}\n- policy: {p.decision} ({p.reason})\n- mode: stub"
