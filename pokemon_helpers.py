FRLG_VERSIONS = {"firered", "leafgreen"}

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


def pretty_location_area(name: str) -> str:
    # Example: "viridian-forest-area" -> "Viridian Forest Area"
    return name.replace("-", " ").title()


def extract_evolution_stages(chain_node: dict) -> list[list[str]]:
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


def text_color_for_bg(hex_color: str) -> str:
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