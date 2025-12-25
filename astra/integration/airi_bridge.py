from __future__ import annotations


def airi_status() -> str:
    # Sprint 1: tylko handshake. Sprint 2: tools API + memory + policies.
    try:
        from airi import __version__ as airi_version
    except Exception as exc:  # pragma: no cover
        return f"! AIRI unavailable: {exc}"

    return f"- AIRI online (version {airi_version})\n- policy: SAFE default\n- mode: stub"
