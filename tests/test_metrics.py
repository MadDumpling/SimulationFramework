from metrics import Metric


def test_metric_update():

    metric = Metric(
        "FPS"
    )

    metric.update(
        144
    )

    assert (
        metric.value
        == 144
    )


def test_metric_history():

    metric = Metric(
        "Speed",
        graph=True,
    )

    metric.update(
        1.0
    )

    metric.update(
        2.0
    )

    metric.update(
        3.0
    )

    assert list(
        metric.history
    ) == [
        1.0,
        2.0,
        3.0,
    ]