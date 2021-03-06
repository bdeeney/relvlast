from datetime          import datetime
from genshi.filters    import Transformer
from logbook           import TestHandler
from persistent        import Persistent
from werkzeug.utils    import cached_property
from werkzeug.routing  import EndpointPrefix
from ramverk.fullstack import Environment, TemplateContext, Application
from ramverk.genshi    import HTMLTemplate


class Root(Persistent):

    greeting = 'Welcome'


class TestEnvironment(Environment):

    @cached_property
    def db(self):
        return self.persistent.setdefault('root', Root())


class TestTemplateContext(TemplateContext):

    injected = 42


class TestApp(Application):

    environment = TestEnvironment

    template_context = TestTemplateContext

    def configure(self):
        self.log_handler = TestHandler()
        self.renderers['.html'].dialect = HTMLTemplate
        self.scan('tests.app.frontend', value=666)
        self.scan('tests.app.module', submount='/module')
        self.scan('tests.app.subdomain', subdomain='en',
                  rulefactory=(EndpointPrefix, 'en_'))

    def filter_genshi_stream(self, environment, template, stream):
        if template.filename == 'filtering.html':
            return stream | Transformer('p/text()').replace('Filtered')
        return stream

    def _JSONMixin__default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(TestApp, self)._JSONMixin__default(obj)
