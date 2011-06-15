from inspect        import isclass
from werkzeug.utils import import_string
from paver.easy     import options, Bunch, task, sh, pushd, path, info
from paver.tasks    import help
from paver.doctools import doc_clean, html
from ramverk.paver  import serve, shell


options.ramverk = Bunch(app='relvlast:Relvlast')
options.sphinx  = Bunch(builddir='../build')


@task
def cover():
    """Measure test coverage."""
    sh('coverage run -m attest')
    sh('coverage report')
    sh('coverage html')


@task
def import_words():
    """Import data exported to XML from jbovlaste."""
    from relvlast.importing import words_from_xml
    from relvlast.objects   import Root

    app = import_string(options.ramverk.app)
    if isclass(app):
        app = app()

    for source in path('exports').files('*.xml'):
        locale = source.stripext().basename()
        info('importing ' + locale)
        with app:
            if locale not in app.root_object:
                app.root_object[locale] = Root()
            app.root_object[locale].words = words_from_xml(source)


@task
def deploy():
    """Deploy to ep.io."""
    with pushd('relvlast/compiled'):
        sh('pyscss -o main.css main.scss')
    sh('epio upload')


@task
def localedata():
    """Install custom locale data for Babel."""
    import yaml, babel, copy, cPickle as pickle
    for source in path('localedata').files('*.yml'):
        data = copy.deepcopy(babel.localedata.load('en'))
        babel.localedata.merge(data, yaml.load(source.bytes()))
        with pushd(babel.localedata._dirname):
            target = source.stripext().basename() + '.dat'
            with open(target, 'wb') as stream:
                info('writing ' + target)
                pickle.dump(data, stream, -1)


@task
def translations():
    sh('pybabel extract -F babel.ini -o messages.pot relvlast')
    sh('pybabel update -i messages.pot -d relvlast/translations')
    sh('pybabel compile -d relvlast/translations')
