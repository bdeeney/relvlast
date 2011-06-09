from contextlib       import contextmanager
from werkzeug.test    import Client, create_environ
from ZODB.DemoStorage import DemoStorage
from fudge            import clear_calls, verify
from tests.app        import TestApp


@contextmanager
def testapp():
    app = TestApp(storage=DemoStorage)
    app.bind_to_environ(create_environ())
    yield app


@contextmanager
def wsgiclient():
    with testapp() as app:
        yield Client(app, app.response)


@contextmanager
def mocking():
    clear_calls()
    try:
        yield
    finally:
        verify()
