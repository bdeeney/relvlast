from __future__        import absolute_import
from genshi.filters    import Transformer
from genshi.input      import HTML
from genshi.template   import TemplateLoader, MarkupTemplate, NewTextTemplate
from werkzeug.utils    import cached_property
from ramverk.rendering import TemplatingMixinBase

try:
    from compactxml import expand_to_string
except ImportError:
    pass


class CompactTemplate(MarkupTemplate):
    """A :class:`~genshi.template.markup.MarkupTemplate` parsing with
    :term:`Compact XML` using preconfigured namespace prefixes."""

    namespaces = dict(
        py='http://genshi.edgewall.org/',
        xi='http://www.w3.org/2001/XInclude')
    """Mapping of namespace prefixes to namespace URIs to be included in
    templates, by default including `py` and `xi`."""

    pretty_print = True
    """Whether the rendered markup should be pretty-printed with
    whitespace."""

    def __init__(self, source, filepath=None, filename=None, loader=None,
                 encoding=None, lookup='strict', allow_exec=True):
        if hasattr(source, 'render'):
            source = source.render()
        source = expand_to_string(source, self.namespaces,
                                  prettyPrint=self.pretty_print)
        super(CompactTemplate, self).__init__(source,
            filepath=filepath, filename=filename, loader=loader,
            encoding=encoding, lookup=lookup, allow_exec=allow_exec)


class CompactHTMLTemplate(CompactTemplate):
    """Like :class:`CompactTemplate` with the extra namespace prefixes
    `i18n` (for :term:`Babel`) and `form` (for :term:`Flatland`) meant for
    use with the HTML serializer which will strip unused prefixes from the
    output."""

    namespaces = dict(
        py='http://genshi.edgewall.org/',
        xi='http://www.w3.org/2001/XInclude',
        i18n='http://genshi.edgewall.org/i18n',
        form='http://ns.discorporate.us/flatland/genshi')


class HTMLTemplate(MarkupTemplate):
    """A :class:`~genshi.template.markup.MarkupTemplate` parsing with
    :class:`~genshi.input.HTMLParser`."""

    def __init__(self, source, filepath=None, filename=None, loader=None,
                 encoding=None, lookup='strict', allow_exec=True):
        if hasattr(source, 'read'):
            source = source.read()
        elif hasattr(source, 'render'):
            source = source.render()
        stream = self.filter_html_stream(HTML(source))
        source = stream.render()
        super(HTMLTemplate, self).__init__(source,
            filepath=filepath, filename=filename, loader=loader,
            encoding=encoding, lookup=lookup, allow_exec=allow_exec)

    def filter_html_stream(self, stream):
        """Apply filters to the HTML `stream`; this happens earlier than
        the usual markup stream which has to be well-formed XML. The
        default injects the namespace prefixes `py`, `xi`, `i18n` (for
        :term:`Babel`) and `form` (for :term:`Flatland`). The HTML
        serializer will later strip unused prefixes from the output."""
        return stream | (Transformer('//html')
            .attr('xmlns:py', 'http://genshi.edgewall.org/')
            .attr('xmlns:xi', 'http://www.w3.org/2001/XInclude')
            .attr('xmlns:i18n', 'http://genshi.edgewall.org/i18n')
            .attr('xmlns:form', 'http://ns.discorporate.us/flatland/genshi'))


class GenshiRenderer(object):
    """Genshi renderer with fixed configuration."""

    serializer = None
    """The method to use when serializing the stream."""

    doctype = None
    """Set a doctype for rendered documents."""

    mimetype = None
    """Set a mimetype on the returned response object."""

    dialect = None
    """Template class if not :class:`CompactTemplate`."""

    lazy = False
    """Serialize lazily, can misbehave with databases."""

    def __init__(self, app, serializer=None, doctype=None,
                 mimetype=None, dialect=CompactTemplate, lazy=False):
        self.app, self.serializer, self.doctype = app, serializer, doctype
        self.mimetype, self.dialect, self.lazy = mimetype, dialect, lazy

    def __call__(self, environment, template_name, **context):
        self.app.update_template_context(environment, context)
        template = self.app.genshi_loader.load(template_name, cls=self.dialect)
        stream = template.generate(**context)
        stream = self.filter(environment, template, stream)
        serialize = stream.serialize if self.lazy else stream.render
        if self.doctype is None:
            rendering = serialize(self.serializer)
        else:
            rendering = serialize(self.serializer, doctype=self.doctype)
        return self.app.response(rendering, mimetype=self.mimetype)

    def filter(self, environment, template, stream):
        """Called to filter the `stream` for `template`, delegating to
        :meth:`~GenshiMixin.filter_genshi_stream` by default."""
        return self.app.filter_genshi_stream(environment, template, stream)

    def __repr__(self): #pragma: no cover
        attrs = ('{0}={1!r}'.format(k, v)
                 for (k, v) in vars(self).iteritems()
                 if k != 'app' and v)
        return 'GenshiRenderer({0})'.format(', '.join(attrs))


class GenshiMixin(TemplatingMixinBase):
    """Add Genshi templating to an application."""

    @cached_property
    def renderers(self):
        R = GenshiRenderer
        renderers = super(GenshiMixin, self).renderers
        renderers.update({
            '.html' : R(self, 'html', 'html5',   'text/html', CompactHTMLTemplate),
            '.xhtml': R(self, 'xml',  'xhtml11', 'application/xhtml+xml'),
            '.atom' : R(self, 'xml',   None,     'application/atom+xml'),
            '.svg'  : R(self, 'xml',  'svg',     'image/svg+xml'),
            '.xml'  : R(self, 'xml',   None,     'application/xml'),
            '.txt'  : R(self, 'text',  None,     'text/plain', NewTextTemplate)
        })
        return renderers

    @cached_property
    def template_loaders(self):
        """Adds a :func:`~genshi.template.loader.package` loader for the
        :file:`{application module}/templates` directory."""
        loaders = super(GenshiMixin, self).template_loaders
        loaders.genshi = [TemplateLoader.package(self.module, 'templates')]
        return loaders

    @cached_property
    def genshi_loader(self):
        """The ``template_loaders.genshi`` loaders wrapped in a
        :class:`~genshi.template.loader.TemplateLoader`."""
        return TemplateLoader(self.template_loaders.genshi,
                              auto_reload=self.settings.debug,
                              callback=self.configure_genshi_template)

    def configure_genshi_template(self, template):
        """Called when `template` is first loaded; override to do Babel and
        Flatland installation and such."""

    def filter_genshi_stream(self, environment, template, stream):
        """Fallback for :meth:`GenshiRenderer.filter`, returning the
        stream unaltered by default."""
        return stream


from ramverk.inventory import members
__all__ = members[__name__]
