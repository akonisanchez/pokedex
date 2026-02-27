from flask import Flask, render_template, request

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

    # Extract the "name" value from URL query string
    # request.args is similar to a dictionaey that contains form data
    name = request.args.get("name")

    return render_template(
        "pokemon.html",
        name=name
    )

# Start the server
if __name__ == "__main__":
    app.run(debug=True)