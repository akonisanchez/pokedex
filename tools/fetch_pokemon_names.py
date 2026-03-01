import json
from pathlib import Path

import requests


def main():
    """
    Fetch all Pokemon names from PokéAPI and save them locally as JSON.
    """
    url = "https://pokeapi.co/api/v2/pokemon?limit=2000&offset=0"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    names = sorted([item["name"] for item in data.get("results", [])])

    out_path = Path("data/pokemon_names.json")
    out_path.write_text(json.dumps(names, indent=2))

    print(f"Saved {len(names)} Pokémon names to {out_path}")


if __name__ == "__main__":
    main()