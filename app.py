from flask import Flask, render_template, request, redirect, url_for
from db import init_db
import requests
import sqlite3

# Create the Pokedex web application
# This represents web server
app = Flask(__name__)

# Initialtize database when app stars
init_db()

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
    return render_template("index.html")

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
    
    # Call PokeAPI
    api_url = f"https://pokeapi.co/api/v2/pokemon/{name}"
    response = requests.get(api_url, timeout = 10)

    # Handle "not found" (or other non-200 responses)
    if response.status_code != 200:
        return render_template(
            "pokemon.html",
            error=f"No Pokemon found for '{name}'. Try another name.",    
        )
    
    data = response.json()

    pokemon = {
        "name": data["name"].title(),
        "height": data["height"],
        "weight": data["weight"],
        "sprite": data["sprites"] ["front_default"],

        # Ex: ["Grass"] or if multiple types ["Grass", "Fighting"]
        "types": [t["type"] ["name"].title() for t in data ["types"]],

        # Ex: [{"name": "HP", "value": 45}, ...]
        "stats": [
            {"name": s["stat"] ["name"].replace("-", " ").title(), "value": s["base_stat"]}
            for s in data["stats"]
        ],
    }

    # Build per-type style info for the template
    type_styles = {}
    for t in pokemon["types"]:
        bg = TYPE_COLORS.get(t, "#6c757d")  # fallback gray
        type_styles[t] = {"bg": bg, "fg": _text_color_for_bg(bg)}

    return render_template("pokemon.html", pokemon=pokemon, type_styles=type_styles)

@app.get("/favorites")
def show_favorites():
    """
    Display all saved favorite Pokemon.
    """

    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM favorites ORDER BY name")
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

    # Get Pokemon name from submitted form data
    pokemon_name = request.form.get("name", "").strip().lower()

    # Guard against empty submissions
    if not pokemon_name:
        return redirect(url_for("pokedex_home"))

    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    try:
        # INSERT OR IGNORE prevents duplicate entries
        cursor.execute(
            "INSERT OR IGNORE INTO favorites (name) VALUES (?)",
            (pokemon_name,)
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
    pokemon_name = request.form.get("name", "").strip().lower()

    if not pokemon_name:
        return redirect(url_for("show_favorites"))

    conn = sqlite3.connect("pokedex.db")
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM favorites WHERE name = ?", (pokemon_name,))
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("show_favorites"))

# Start the server
if __name__ == "__main__":
    app.run(debug=True)