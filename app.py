from flask import Flask, render_template, request

# Create the Pokedex web application
app = Flask(__name__)

# Pokedex Homepage route
# This runs when someone visits the root URL
@app.get("/")
def pokedex_home():
    return render_template("index.html")

# Show Pokemon route
# This runs when browser visits /pokemon
@app.get("/pokemon")
def show_pokemon():
    name = request.args.get("name")

    return f"""
    <h1>You searched for: {name}</h1>
    <p>This is where Pokemon data will appear.</p>
    <a href="/">Go back </a>
    """

# Start the server
if __name__ == "__main__":
    app.run(debug=True)