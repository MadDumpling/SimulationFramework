import json


def save_preset(
    simulation,
    filepath,
):

    data = {
        "simulation": simulation.name,
        "version": simulation.version,
        "parameters": simulation.serialize(),
    }

    with open(
        filepath,
        "w",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
        )


def load_preset(
    simulation,
    filepath,
):

    with open(
        filepath,
        "r",
    ) as file:

        data = json.load(file)

    simulation.deserialize(
        data["parameters"]
    )
