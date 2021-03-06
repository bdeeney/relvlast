from werkzeug.exceptions import NotFound
from werkzeug.utils      import cached_property
from ramverk.utils       import Alias, Configurable


class BaseEnvironment(Configurable):
    """Environment base class."""

    def __init__(self, application, environ):

        self.application = application
        """Application that received the request of this environment."""

        self.environ = environ
        """WSGI environment."""

        self.__create__()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __call__(self):
        """Respond to this request or raise an HTTP exception. Default
        raises a :exc:`~werkzeug.exceptions.NotFound`."""
        raise NotFound

    @cached_property
    def request(self):
        """A :attr:`~ramverk.application.BaseApplication.request` wrapping
        this :attr:`environ`."""
        return self.application.request(self.environ)

    response = Alias('application.response',
                     ':attr:`~ramverk.application.BaseApplication.response`')


from ramverk.inventory import members
__all__ = members[__name__]
