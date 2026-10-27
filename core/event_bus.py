class EventBus:

    def __init__(self):

        self.listeners = {}

    def subscribe(
        self,
        event,
        callback,
    ):

        self.listeners.setdefault(
            event,
            []
        ).append(callback)

    def publish(
        self,
        event,
        *args,
        **kwargs,
    ):

        for callback in self.listeners.get(
            event,
            []
        ):
            callback(
                *args,
                **kwargs
            )