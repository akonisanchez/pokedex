import os
import requests
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-i/red-blue"
OUT_DIR = Path("static/sprites/gen1-red-blue")

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for i in range(1, 152):
        url = f"{BASE_URL}/{i}.png"
        out_path = OUT_DIR / f"{i}.png"

        if out_path.exists():
            continue

        r = requests.get(url, timeout=20)
        r.raise_for_status()
        out_path.write_bytes(r.content)

        if i % 25 == 0:
            print(f"Downloaded up to {i}...")

    print("Done. Sprites saved to:", OUT_DIR)

if __name__ == "__main__":
    main()