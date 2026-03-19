from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import init_db, get_conn
from cache_utils import cache_get, cache_set
from pokeapi import load_kanto_pokemon, get_frlg_encounters_from_url, get_evolution_chain

from pokemon_helpers import TYPE_COLORS, text_color_for_bg

import random
import requests
import sqlite3
import os
import json
from pathlib import Path


app = Flask(__name__)

# Use an environment variable in production, with a local fallback for development.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

init_db()

# Load Pokemon names once for autocomplete and homepage display.
NAMES_PATH = Path("data/pokemon_names.json")
POKEMON_NAMES = []
KANTO_POKEMON = []

if NAMES_PATH.exists():
    POKEMON_NAMES = json.loads(NAMES_PATH.read_text())

try:
    KANTO_POKEMON = load_kanto_pokemon()
except Exception:
    KANTO_POKEMON = []


@app.get("/")
def pokedex_home():
    """Render the homepage."""
    return render_template(
        "index.html",
        pokemon_names=POKEMON_NAMES,
        kanto=KANTO_POKEMON
    )


@app.get("/random")
def random_pokemon():
    """Redirect to a random Pokemon page."""
    if not POKEMON_NAMES:
        return redirect(url_for("pokedex_home"))

    name = random.choice(POKEMON_NAMES)
    return redirect(url_for("show_pokemon", name=name))


@app.get("/pokemon")
def show_pokemon():
    """Display search results for a Pokemon."""
    name = request.args.get("name", "").strip().lower()

    if not name:
        return redirect(url_for("pokedex_home"))

    cache_key = f"pokemon:{name}"
    data = cache_get(cache_key)

    if data is None:
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
        "sprite": data["sprites"]["front_default"],
        "types": [t["type"]["name"].title() for t in data["types"]],
        "stats": [
            {
                "name": s["stat"]["name"].replace("-", " ").title(),
                "value": s["base_stat"]
            }
            for s in data["stats"]
        ],
    }

    encounters_url = data.get("location_area_encounters")
    frlg_encounters = get_frlg_encounters_from_url(encounters_url)
    evolution_stages = get_evolution_chain(name)

    type_styles = {}
    for t in pokemon["types"]:
        bg = TYPE_COLORS.get(t, "#6c757d")
        type_styles[t] = {"bg": bg, "fg": text_color_for_bg(bg)}

    is_favorite = False

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
    """Display the logged-in user's favorite Pokemon."""
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
    """Add a Pokemon to the logged-in user's favorites."""
    if "user_id" not in session:
        return redirect(url_for("login_form"))

    pokemon_name = request.form.get("name", "").strip().lower()

    if not pokemon_name:
        return redirect(url_for("pokedex_home"))

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # Prevent duplicate favorites for the same user.
        cursor.execute(
            "INSERT OR IGNORE INTO favorites (user_id, pokemon_name) VALUES (?, ?)",
            (session["user_id"], pokemon_name),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("show_favorites"))


@app.post("/favorites/remove")
def remove_favorite():
    """Remove a Pokemon from the logged-in user's favorites."""
    if "user_id" not in session:
        return redirect(url_for("login_form"))

    pokemon_name = request.form.get("name", "").strip().lower()

    if not pokemon_name:
        return redirect(url_for("show_favorites"))

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM favorites WHERE user_id = ? AND pokemon_name = ?",
            (session["user_id"], pokemon_name),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("show_favorites"))


# Auth routes
@app.get("/register")
def register_form():
    """Render the registration form."""
    return render_template("register.html")


@app.post("/register")
def register_user():
    """Create a new user account."""
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
    """Render the login form."""
    return render_template("login.html")


@app.post("/login")
def login_user():
    """Authenticate a user and start a session."""
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
    """Log out the current user."""
    session.clear()
    return redirect(url_for("pokedex_home"))


if __name__ == "__main__":
    app.run(debug=True)