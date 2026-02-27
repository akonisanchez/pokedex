from flask import Flask

# Create the Pokedex web application
app = Flask(__name__)

# Pokedex Homepage route
# This runs when someone visits the root URL
@app.get("/")
def pokedex_home():
    return """
    <h1>Pokedex</h1>
    <p>Welcome, Trainer.</p>
    <p>Your journey to become a Pokemon Master begins here.</p>
    """

# Start the server
if __name__ == "__main__":
    app.run(debug=True)