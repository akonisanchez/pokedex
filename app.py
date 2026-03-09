from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import init_db, get_conn
import random
import requests
import sqlite3
import os
import time 
from typing import Any
import json
from pathlib import Path

# Create the Pokedex web application
# This represents web server
app = Flask(__name__)

# Deployment-safe session signing key:
# - In production, set SECRET_KEY as an environment variable.
# - Locally, we fall back to a dev-only value.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

# Initialtize database when app stars
init_db()

# Load Pokemon names once for fast autocomplete on the homepage
NAMES_PATH = Path("data/pokemon_names.json")
POKEMON_NAMES = []
KANTO_POKEMON = []

if NAMES_PATH.exists():
    POKEMON_NAMES = json.loads(NAMES_PATH.read_text())

FRLG_VERSIONS = {"firered", "leafgreen"}

# In-memory cache to reduce repeated PokéAPI calls.
# Key -> (expires_at, value)
CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 60 * 10  # 10 minutes

def cache_get(key: str):
    item = CACHE.get(key)
    if not item:
        return None
    expires_at, value = item
    if time.time() > expires_at:
        CACHE.pop(key, None)
        return None
    return value


def cache_set(key: str, value, ttl: int = CACHE_TTL_SECONDS):
    CACHE[key] = (time.time() + ttl, value)

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

try:
    KANTO_POKEMON = load_kanto_pokemon()
except Exception:
    KANTO_POKEMON = []

def _pretty_location_area(name: str) -> str:
    # Example: "viridian-forest-area" -> "Viridian Forest Area"
    return name.replace("-", " ").title()

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
                results[version_name].add(_pretty_location_area(loc_area))

    results_list = {k: sorted(list(v)) for k, v in results.items() if v}
    final = results_list if results_list else None
    cache_set(cache_key, final)
    return final

def _extract_evolution_stages(chain_node: dict) -> list[list[str]]:
    """
    Convert PokéAPI evolution chain structure into stage-based rows.

    Output example (branching):
      [
        ["eevee"],
        ["vaporeon", "jolteon", "flareon", ...]
      ]

    Output example (linear):
      [
        ["bulbasaur"],
        ["ivysaur"],
        ["venusaur"]
      ]
    """
    stages: list[list[str]] = []
    current_level = [chain_node]

    while current_level:
        stage_names: list[str] = []
        next_level: list[dict] = []

        for node in current_level:
            species = node.get("species", {})
            name = species.get("name")
            if name:
                stage_names.append(name)

            next_level.extend(node.get("evolves_to", []))

        # Deduplicate and sort for stable display
        stage_names = sorted(set(stage_names))
        if stage_names:
            stages.append(stage_names)

        current_level = next_level

    return stages


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
    
    stages = _extract_evolution_stages(chain)
    cache_set(cache_key, stages)
    return stages

# Pokemon type colors 
TYPE_COLORS = {
    "Normal": "#A8A77A",
    "Fire": "#EE8130",
    "Water": "#6390F0",
    "Electric": "#F7D02C",
    "Grass": "#7AC74C",
    "Ice": "#96D9D6",
    "Fighting": "#C22E28",
    "Poison": "#A33EA1",
    "Ground": "#E2BF65",
    "Flying": "#A98FF3",
    "Psychic": "#F95587",
    "Bug": "#A6B91A",
    "Rock": "#B6A136",
    "Ghost": "#735797",
    "Dragon": "#6F35FC",
    "Dark": "#705746",
    "Steel": "#B7B7CE",
    "Fairy": "#D685AD",
}


def _text_color_for_bg(hex_color: str) -> str:
    """
    Black/white text for readability based on background color brightness.
    Keeps badges readable without manually tuning each type.
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Perceived luminance 
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "#111111" if luminance > 165 else "#ffffff"

# Pokedex Homepage route
# This runs when someone visits the root URL and renders the main search page
@app.get("/")
def pokedex_home():
    # Kanto dex (first 151) for homepage scroller
    kanto = KANTO_POKEMON
    return render_template(
        "index.html", 
        pokemon_names=POKEMON_NAMES,
        kanto=kanto
    )

# Returns a random Pokemon
@app.get("/random")
def random_pokemon():
    """
    Redirect to a random Pokemon result page.

    Uses the locally cached Pokemon name list 
    """
    if not POKEMON_NAMES:
        return redirect(url_for("pokedex_home"))

    name = random.choice(POKEMON_NAMES)
    return redirect(url_for("show_pokemon", name=name))

# Pokemon search results route
# This runs when user submits the search form
# Will read the Pokemon name from the URL query parameters
# Example url: /pokemon?name=jigglypuff
@app.get("/pokemon")
def show_pokemon():
    """
    Display Pokemon search results.

    - Reads the Pokemon name from the quesry string (?name=jigglypuff)
    - Calls PokeAPI to fetch real data
    -Renders a template with Pokemon details or an error message
    """

    # Normalize user input so searches are consistent
    name = request.args.get("name", "").strip().lower()

    # If someone visits /pokemon with no query param, send them home
    if not name:
        return redirect(url_for("pokedex_home"))

    cache_key = f"pokemon:{name}"
    data = cache_get(cache_key)

    if data is None:
        # Call PokeAPI
        api_url = f"https://pokeapi.co/api/v2/pokemon/{name}"
        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            return render_template(
                "pokemon.html", 
                error=f"No Pokemon found for '{name}'. Try another name."
            )
    
        data = response.json()
        cache_set(cache_key, data)

    pokemon = {
        "name": data["name"].title(),
        "sprite": data["sprites"] ["front_default"],

        # Ex: ["Grass"] or if multiple types ["Grass", "Fighting"]
        "types": [t["type"] ["name"].title() for t in data ["types"]],

        # Ex: [{"name": "HP", "value": 45}, ...]
        "stats": [
            {"name": s["stat"] ["name"].replace("-", " ").title(), "value": s["base_stat"]}
            for s in data["stats"]
        ],
    }
    
    encounters_url = data.get("location_area_encounters")
    frlg_encounters = get_frlg_encounters_from_url(encounters_url)
    evolution_stages = get_evolution_chain(name)

    # Build per-type style info for the template
    type_styles = {}
    for t in pokemon["types"]:
        bg = TYPE_COLORS.get(t, "#6c757d")  # fallback gray
        type_styles[t] = {"bg": bg, "fg": _text_color_for_bg(bg)}
    
    # Check whether this Pokemon is already saved as a favorite
    # Default: not favorited
    is_favorite = False

    # Only check favorites if the user is logged in
    if "user_id" in session:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND pokemon_name = ? LIMIT 1",
            (session["user_id"], name),
        )
        is_favorite = cursor.fetchone() is not None
        conn.close()

    return render_template(
        "pokemon.html", 
        pokemon=pokemon, 
        type_styles=type_styles,
        is_favorite=is_favorite,
        evolution_stages=evolution_stages,
        frlg_encounters=frlg_encounters,
        )

@app.get("/favorites")
def show_favorites():
    """
    Display all saved favorite Pokemon.
    """

    if "user_id" not in session:
        return redirect(url_for("login_form"))

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT pokemon_name FROM favorites WHERE user_id = ? ORDER BY pokemon_name",
        (session["user_id"],)
    )
    rows = cursor.fetchall()
    conn.close()

    favorites = [{"raw": row[0], "display": row[0].title()} for row in rows]
    return render_template("favorites.html", favorites=favorites)

@app.post("/favorites/add")
def add_favorite():
    """
    Save a Pokemon to the favorites database.

    This route receives a POST request from the results page form
    and inserts the Pokemon name into the favorites table.
    """

    if "user_id" not in session:
        return redirect(url_for("login_form"))

    # Get Pokemon name from submitted form data
    pokemon_name = request.form.get("name", "").strip().lower()

    # Guard against empty submissions
    if not pokemon_name:
        return redirect(url_for("pokedex_home"))

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # INSERT OR IGNORE prevents duplicate entries
        cursor.execute(
            "INSERT OR IGNORE INTO favorites (user_id, pokemon_name) VALUES (?, ?)",
            (session["user_id"], pokemon_name),
        )
        conn.commit()
    finally:
        conn.close()

    # Redirect user to favorites page after saving
    return redirect(url_for("show_favorites"))

@app.post("/favorites/remove")
def remove_favorite():
    """
    Remove a Pokemon from favorites.

    Receives a POST request from the favorites page and deletes
    the Pokemon name from the favorites table.
    """

    if "user_id" not in session:
        return redirect(url_for("login_form"))
    
    pokemon_name = request.form.get("name", "").strip().lower()

    if not pokemon_name:
        return redirect(url_for("show_favorites"))

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM favorites WHERE user_id = ? AND pokemon_name = ?",
                      (session["user_id"], pokemon_name),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("show_favorites"))

# Auth routes
@app.get("/register")
def register_form():
    return render_template("register.html")


@app.post("/register")
def register_user():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    if not username or not password:
        return render_template("register.html", error="Username and password required.")

    password_hash = generate_password_hash(password)

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return render_template("register.html", error="Username already taken.")

    conn.close()
    return redirect(url_for("login_form"))


@app.get("/login")
def login_form():
    return render_template("login.html")


@app.post("/login")
def login_user():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return render_template("login.html", error="Invalid username or password.")

    user_id, password_hash = row
    if not check_password_hash(password_hash, password):
        return render_template("login.html", error="Invalid username or password.")

    session["user_id"] = user_id
    session["username"] = username
    return redirect(url_for("pokedex_home"))


@app.post("/logout")
def logout_user():
    session.clear()
    return redirect(url_for("pokedex_home"))

# Start the server
if __name__ == "__main__":
    app.run(debug=True)