from flask import Flask, render_template, request, redirect, url_for
import requests

# Create the Pokedex web application
# This represents web server
app = Flask(__name__)

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
    }

    return render_template("pokemon.html", pokemon=pokemon)

# Start the server
if __name__ == "__main__":
    app.run(debug=True)