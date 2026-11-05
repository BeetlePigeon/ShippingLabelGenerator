import error_logging
import logging


if __name__ == '__main__':
    try:
        from gui import GUI
        app = GUI()
        app.run()

    except Exception:
        logging.exception("Unhandled application exception")
        raise