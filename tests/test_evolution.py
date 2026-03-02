from app import _extract_evolution_stages


def test_extract_evolution_stages_linear_chain():
    # bulbasaur -> ivysaur -> venusaur
    chain = {
        "species": {"name": "bulbasaur"},
        "evolves_to": [
            {
                "species": {"name": "ivysaur"},
                "evolves_to": [
                    {"species": {"name": "venusaur"}, "evolves_to": []}
                ],
            }
        ],
    }

    stages = _extract_evolution_stages(chain)

    assert stages == [["bulbasaur"], ["ivysaur"], ["venusaur"]]


def test_extract_evolution_stages_branching_chain():
    # eevee -> vaporeon / jolteon / flareon
    chain = {
        "species": {"name": "eevee"},
        "evolves_to": [
            {"species": {"name": "vaporeon"}, "evolves_to": []},
            {"species": {"name": "jolteon"}, "evolves_to": []},
            {"species": {"name": "flareon"}, "evolves_to": []},
        ],
    }

    stages = _extract_evolution_stages(chain)

    assert stages[0] == ["eevee"]
    assert stages[1] == ["flareon", "jolteon", "vaporeon"]  # sorted