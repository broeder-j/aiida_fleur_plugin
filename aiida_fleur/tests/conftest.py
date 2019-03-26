from __future__ import absolute_import
from __future__ import print_function
import pytest
from aiida.manage.fixtures import fixture_manager

@pytest.fixture(scope='session')
def aiida_env():
    with fixture_manager() as manager:
        yield manager

@pytest.fixture()
def fresh_aiida_env(aiida_env):
    yield
    aiida_env.reset_db()

def test_my_stuff(fresh_aiida_env):
   # run a test
   print('test_my_stuf works')
