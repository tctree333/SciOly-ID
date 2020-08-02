from sciolyid import setup as _setup


def setup(*args, **kwargs):
    if len(args) == 1 and isinstance(args[0], dict):
        kwargs = args[0]
    kwargs["web"] = True
    _setup(kwargs)


def get_app():
    from sciolyid.web.main import app  # pylint: disable=import-outside-toplevel

    return app
