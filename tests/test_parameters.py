from parameters import Parameter


def test_parameter_creation():

    parameter = Parameter(
        "Gravity",
        9.8,
        0.0,
        20.0,
    )

    assert parameter.name == "Gravity"
    assert parameter.value == 9.8
    assert parameter.min == 0.0
    assert parameter.max == 20.0