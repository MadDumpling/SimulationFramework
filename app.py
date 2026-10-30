from ui import (
    Application,
    DesignerApplication,
)


def main():

    app = Application()

    app.initialize()

    designer_app = DesignerApplication()

    designer_app.initialize()

    while (
        designer_app.running
        and app.running()
    ):

        designer_app.update()

        designer_app.render()

        app.render()

    app.shutdown()


if __name__ == "__main__":
    main()
