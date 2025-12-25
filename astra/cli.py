from __future__ import annotations

import argparse

from .integration.airi_bridge import airi_status

MENU = [
    ("1", "Ustawienia", "settings"),
    ("2", "Udaj się na mostek", "bridge"),
    ("3", "Udaj się do AIRI", "airi"),
    ("4", "Uniwersum (Czym jest ASTRA?)", "lore"),
    ("0", "Wyjście", "exit"),
]


def _print_menu() -> None:
    print("=== ASTRA HUB (Sprint 1) ===")
    for key, label, _ in MENU:
        print(f"[{key}] {label}")


def _handle(choice: str) -> int:
    choice = choice.strip()

    if choice == "1":
        print("USTAWIENIA (stub)")
        print("- profil: local-first")
        print("- polityka: SAFE default")
        return 0

    if choice == "2":
        print("MOSTEK (stub)")
        print("- status okrętu: brak danych (Sprint 1)")
        return 0

    if choice == "3":
        print("AIRI (bridge)")
        print(airi_status())
        return 0

    if choice == "4":
        print("UNIWERSUM / CANON (Sprint 1)")
        print(
            "ASTRA: międzygwiezdny statek kolonizacyjny z sektorami badawczymi.\n"
            "Po przejściu przez czarną dziurę kontakt zniknął; po drugiej stronie\n"
            "anomalia (biała dziura) zapadła się i zniknęła, uszkadzając okręt.\n"
            "AIRI: dawna AI/hologram okrętowa, która uległa materializacji jako\n"
            "cyfrowe życie (model JA + cele + pamięć + refleksja + inicjatywa)."
        )
        return 0

    if choice == "0":
        print("Do zobaczenia.")
        return 0

    print("Nieznana opcja.")
    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="astra")
    p.add_argument(
        "--once",
        choices=[m[0] for m in MENU],
        help="Uruchom jedną opcję menu i zakończ.",
    )
    ns = p.parse_args(argv)

    if ns.once:
        return _handle(ns.once)

    while True:
        _print_menu()
        choice = input("> ")
        code = _handle(choice)
        if choice.strip() == "0":
            return code
