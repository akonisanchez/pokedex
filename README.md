# Pokédex Scanner

A Flask web app built in celebration of Pokémon’s 30th anniversary. It started as a way to practice building a real web product around an external API, then turned into a practical companion for my Pokémon LeafGreen run so I could quickly scan a Pokémon and see key details, evolution stages, and where it can be found in game.

**Live Demo:** https://pokedex-scanner.onrender.com/
Note: the first load can take a minute if the service is waking up.

## Persistence Note (Demo)
This app uses SQLite for simplicity. On deployed demo, data (i.e., accounts/favorites) may reset after a redeploy or server restart.

## Features

* Scan any Pokémon by name using PokéAPI data
* Kanto Dex sprite scroller with classic Gen 1 Red and Blue sprites
* Wild Encounter button for quick random scans
* Evolution chain shown as stage rows, including branching lines
* FireRed and LeafGreen wild encounter locations when available
* Accounts with register, login, and logout
* Per user favorites with add and remove flows

## Demo

**Home**
![Home](docs/home.png)

**Kanto sprite scan**
<img src="docs/sprite_scan.gif" alt="Kanto sprite scan" width="700">

**Search**
![Search](docs/search_feature.gif)

**Wild Encounter**
![Wild encounter](docs/wild_encounter.gif)

**Register and login**
![Auth](docs/register_login_display.gif)

**Favorites**
![Favorites](docs/test.gif)

**Evolution chain**
![Evolution](docs/evolution_display.gif)

## Tech Stack

* Python
* Flask with Jinja templates
* Requests for HTTP
* SQLite for persistence
* Bootstrap 5 plus custom CSS device shell
* pytest unit tests

## What I learned

* How to design and ship a full stack feature from UI to database, including auth and per user data
* How to work with external APIs reliably, including timeouts, caching, and performance tradeoffs
* How to structure iterative improvements through small PRs and clean commits
* How to polish UX through responsive styling and a consistent visual system

## Getting Started

### 1) Clone repo & create virtual environment
```bash
git clone https://github.com/akonisanchez/pokedex.git
cd pokedex
python3 -m venv venv
source venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run the app
```bash
python3 app.py
```
