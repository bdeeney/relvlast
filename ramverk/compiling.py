from werkzeug.routing import Rule
from werkzeug.utils   import cached_property
from ramverk.routing  import URLMapMixin


def compiled(segments, compilers):
    filename = segments.name
    compiler_name = filename[filename.index('.'):]
    compiler = compilers[compiler_name]
    return compiler(filename)


class CompilerMixinBase(URLMapMixin):
    """Base class for compiler mixins."""

    def __create__(self):
        self.route(Rule('/compiled/<path:name>', endpoint='compiled'))
        self.endpoints['compiled'] = compiled
        super(CompilerMixinBase, self).__create__()

    @cached_property
    def compilers(self):
        """Mapping of output file extensions to compilers."""
        return {}
