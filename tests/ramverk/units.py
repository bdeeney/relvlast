from __future__          import absolute_import
from attest              import Tests, assert_hook, raises
from fudge               import Fake
from werkzeug.wrappers   import BaseResponse
from ramverk.application import BaseApplication
from ramverk.transaction import TransactionMixin
from ramverk.utils       import Bunch
from ramverk.wrappers    import ResponseUsingMixin
from tests               import mocking


unit = Tests()
mock = Tests(contexts=[mocking])


@unit.test
def bunch_attrs_and_items_are_same():

    bunch = Bunch(answer=42)
    assert bunch.answer is bunch['answer'] == 42

    del bunch.answer
    assert 'answer' not in bunch and not hasattr(bunch, 'answer')

    bunch.answer = 42
    assert bunch.answer is bunch['answer'] == 42

    del bunch['answer']
    assert 'answer' not in bunch and not hasattr(bunch, 'answer')


@mock.test
def successful_transaction():

    class App(TransactionMixin, BaseApplication):
        transaction_manager =\
            (Fake('TransactionManager')
            .remember_order()
            .expects('begin')
            .expects('isDoomed')
            .returns(False)
            .expects('commit'))

    with App():
        pass


@mock.test
def failed_transaction():

    class App(TransactionMixin, BaseApplication):
        transaction_manager =\
            (Fake('TransactionManager')
            .remember_order()
            .expects('begin')
            .expects('abort'))

    with raises(RuntimeError):
        with App():
            raise RuntimeError


@mock.test
def doomed_transaction():

    class App(TransactionMixin, BaseApplication):
        transaction_manager =\
            (Fake('TransactionManager')
            .remember_order()
            .expects('begin')
            .expects('isDoomed')
            .returns(True)
            .expects('abort'))

    with App():
        pass


@unit.test
def response_using():

    class Response(ResponseUsingMixin, BaseResponse):
        pass

    response = Response('hello').using(status=404)
    assert response.data == 'hello' and response.status_code == 404

    response = Response(headers={'location': 'other-place'})
    response = response.using(headers={'Server': 'some-server'})
    assert response.headers['Location'] == 'other-place'
    assert response.headers['Server'] == 'some-server'

    assert Response().direct_passthrough == False
    assert Response().using().direct_passthrough == False
    response = Response().using(direct_passthrough=True)
    assert response.direct_passthrough == True

    assert Response('hello').using('hi').data == 'hi'
    assert Response('hello').using(['hi']).data == 'hi'

    response = Response(status=300).using(status='404 NOT FOUND')
    assert response.status_code == 404
