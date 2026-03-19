import requests

from cache_utils import cache_get, cache_set
from pokemon_helpers import (
    FRLG_VERSIONS,
    extract_evolution_stages,
    pretty_location_area,
)


def load_kanto_pokemon() -> list[dict]:
    """
    Load the original 151 Pokémon in National Dex order.
    Cached in memory so don't need to refetch on every request.
    """
    url = "https://pokeapi.co/api/v2/pokemon?limit=151&offset=0"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    kanto = []
    for i, item in enumerate(results, start=1):
        kanto.append({"id": i, "name": item["name"]})
    return kanto


def get_frlg_encounters_from_url(encounters_url: str | None) -> dict[str, list[str]] | None:
    """
    Given a location_area_encounters URL, return FireRed/LeafGreen encounter locations.
    Returns None if no FR/LG data found or url missing.
    """
    if not encounters_url:
        return None

    cache_key = f"frlg:{encounters_url}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    enc_resp = requests.get(encounters_url, timeout=10)
    if enc_resp.status_code != 200:
        cache_set(cache_key, None)
        return None

    encounter_rows = enc_resp.json()
    results: dict[str, set[str]] = {"firered": set(), "leafgreen": set()}

    for row in encounter_rows:
        loc_area = (row.get("location_area") or {}).get("name")
        if not loc_area:
            continue

        for vd in row.get("version_details", []):
            version_name = ((vd.get("version") or {}).get("name") or "").lower()
            if version_name in FRLG_VERSIONS:
                results[version_name].add(pretty_location_area(loc_area))

    results_list = {k: sorted(list(v)) for k, v in results.items() if v}
    final = results_list if results_list else None
    cache_set(cache_key, final)
    return final


def get_evolution_chain(pokemon_name: str) -> list[str] | None:
    """
    Given a Pokemon name, fetch and return its evolution chain as a list of names.
    Returns None if any step fails.
    """

    cache_key = f"evo:{pokemon_name}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # 1) Species endpoint (contains evolution chain URL)
    species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}"
    species_resp = requests.get(species_url, timeout=10)
    if species_resp.status_code != 200:
        return None

    species_data = species_resp.json()
    evo_chain_url = (species_data.get("evolution_chain") or {}).get("url")
    if not evo_chain_url:
        return None

    # 2) Evolution chain endpoint
    evo_resp = requests.get(evo_chain_url, timeout=10)
    if evo_resp.status_code != 200:
        return None

    evo_data = evo_resp.json()
    chain = evo_data.get("chain")
    if not chain:
        cache_set(cache_key, None)
        return None
    
    stages = extract_evolution_stages(chain)
    cache_set(cache_key, stages)
    return stages