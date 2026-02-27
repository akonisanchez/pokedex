from flask import Flask, render_template

# Create the Pokedex web application
app = Flask(__name__)

# Pokedex Homepage route
# This runs when someone visits the root URL
@app.get("/")
def pokedex_home():
    return render_template("index.html")

# Start the server
if __name__ == "__main__":
    app.run(debug=True)