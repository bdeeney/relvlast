from __future__          import absolute_import

from logbook             import NestedSetup, NullHandler, StderrHandler
from logbook.more        import ColorizedStderrHandler

from werkzeug.utils      import cached_property
from werkzeug.wrappers   import BaseRequest,\
                                AcceptMixin,\
                                AuthorizationMixin,\
                                CommonRequestDescriptorsMixin,\
                                ETagRequestMixin,\
                                UserAgentMixin
from werkzeug.wrappers   import BaseResponse,\
                                CommonResponseDescriptorsMixin,\
                                ETagResponseMixin,\
                                ResponseStreamMixin,\
                                WWWAuthenticateMixin

from ZODB.FileStorage    import FileStorage

from ramverk.application import BaseApplication
from ramverk.environment import BaseEnvironment
from ramverk.genshi      import GenshiMixin
from ramverk.logbook     import LogbookEnvironmentMixin, LogbookMixin
from ramverk.rendering   import RenderingEnvironmentMixin, JSONMixin
from ramverk.routing     import URLMapAdapterEnvironmentMixin, URLMapMixin
from ramverk.scss        import SCSSMixin
from ramverk.session     import EnvironmentSessionMixin, SessionMixin, SecretKey
from ramverk.transaction import TransactionEnvironmentMixin
from ramverk.venusian    import VenusianMixin
from ramverk.wrappers    import DeferredResponseInitMixin
from ramverk.wsgi        import SharedDataMiddlewareMixin
from ramverk.zodb        import ZODBEnvironmentMixin, ZODBMixin


class Environment(LogbookEnvironmentMixin,
                  EnvironmentSessionMixin,
                  RenderingEnvironmentMixin,
                  TransactionEnvironmentMixin,
                  URLMapAdapterEnvironmentMixin,
                  ZODBEnvironmentMixin,
                  BaseEnvironment):
    """Full-stack environment object."""


class Request(AcceptMixin,
              AuthorizationMixin,
              CommonRequestDescriptorsMixin,
              ETagRequestMixin,
              UserAgentMixin,
              BaseRequest):
    """Full-stack request object."""


class Response(CommonResponseDescriptorsMixin,
               DeferredResponseInitMixin,
               ETagResponseMixin,
               ResponseStreamMixin,
               WWWAuthenticateMixin,
               BaseResponse):
    """Full-stack response object."""

    default_mimetype = 'text/html'
    """Fall back on :mimetype:`text/html` if no mimetype was set."""


class Application(LogbookMixin,
                  ZODBMixin,
                  GenshiMixin,
                  JSONMixin,
                  SCSSMixin,
                  SessionMixin,
                  URLMapMixin,
                  VenusianMixin,
                  SharedDataMiddlewareMixin,
                  BaseApplication):
    """Full-stack application."""

    environment = Environment

    request = Request

    response = Response

    @cached_property
    def settings(self):
        settings = super(Application, self).settings
        settings.storage = lambda: FileStorage(settings.name.lower() + '.db')
        settings.secret_key = SecretKey(settings.name.lower() + '.key')
        return settings

    @cached_property
    def log_handler(self): #pragma: no cover
        """A :class:`~logbook.more.ColorizedStderrHandler` if the `debug`
        setting is true, otherwise only logging warnings and above in plain
        text to stderr."""
        if self.settings.debug:
            return ColorizedStderrHandler(
                format_string='{record.level_name:>8}: '
                              '{record.channel}: {record.message}')
        return NestedSetup([NullHandler(),
                            StderrHandler(level='WARNING')])
