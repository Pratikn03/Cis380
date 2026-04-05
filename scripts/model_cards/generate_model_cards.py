from __future__ import annotations

from app.mlops.model_cards import generate_default_cards


def main() -> None:
    cards = generate_default_cards()
    for path in cards:
        print(f"[model-cards] wrote {path}")


if __name__ == "__main__":
    main()
