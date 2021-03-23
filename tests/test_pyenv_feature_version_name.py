import pytest
from tempenv import TemporaryEnvironment
from test_pyenv_helpers import run_pyenv_test


@pytest.mark.parametrize("command", ['version-name', 'vname'])
def test_no_version(command):
    def commands(ctx):
        assert ctx.pyenv(command) == ("No global python version has been set yet. "
                                      "Please set the global version by typing:\r\n"
                                      "pyenv global 3.7.2")
    run_pyenv_test({}, commands)


@pytest.mark.parametrize("command", ['version-name', 'vname'])
def test_global_version(command):
    def commands(ctx):
        assert ctx.pyenv(command) == "3.7.2"
    run_pyenv_test({'global_ver': "3.7.2"}, commands)


@pytest.mark.parametrize("command", ['version-name', 'vname'])
def test_one_local_version(command):
    def commands(ctx):
        assert ctx.pyenv(command) == "3.9.1"
    settings = {
        'global_ver': "3.7.2",
        'local_ver': "3.9.1"
    }
    run_pyenv_test(settings, commands)


@pytest.mark.parametrize("command", ['version-name', 'vname'])
def test_shell_version(command):
    def commands(ctx):
        assert ctx.pyenv(command) == "3.9.2"
    settings = {
        'global_ver': "3.7.5",
        'local_ver': "3.8.6",
    }
    with TemporaryEnvironment({"PYENV_VERSION": "3.9.2"}):
        run_pyenv_test(settings, commands)
