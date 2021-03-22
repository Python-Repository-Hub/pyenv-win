import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from packaging import version
from pathlib import Path


@contextmanager
def working_directory(path):
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def python_exes(suffixes=None):
    if suffixes is None:
        suffixes = [""]
    else:
        suffixes.append("")
    for suffix in suffixes:
        yield f'python{suffix}.exe'
        yield f'pythonw{suffix}.exe'


def script_exes(ver):
    for suffix in ['', f'{ver.major}', f'{ver.major}{ver.minor}']:
        yield f'pip{suffix}.exe'
    for suffix in ['', f'-{ver.major}.{ver.minor}']:
        yield f'easy_install{suffix}.exe'


def pyenv_setup(settings):
    pyenv_path, local_path, versions, global_ver, local_ver =\
        settings['pyenv_path'],\
        settings['local_path'],\
        settings.get('versions', None),\
        settings.get("global_ver", None),\
        settings.get('local_ver', None)
    if versions is None:
        versions = []
    src_path = Path(__file__).resolve().parents[1].joinpath('pyenv-win')
    dirs = [r'bin', r'libexec\libs', r'shims', r'versions']
    for d in dirs:
        os.makedirs(Path(pyenv_path, d))
    files = [r'bin\pyenv.bat',
             r'libexec\pyenv.vbs',
             r'libexec\libs\pyenv-install-lib.vbs',
             r'libexec\libs\pyenv-lib.vbs']
    for f in files:
        shutil.copy(src_path.joinpath(f), Path(pyenv_path, f))
    versions_dir = Path(pyenv_path, r'versions')

    def touch(exe):
        with open(exe, 'a'):
            os.utime(exe, None)

    def create_pythons(path):
        os.mkdir(path)
        for exe in python_exes([f'{ver.major}', f'{ver.major}{ver.minor}']):
            touch(path.joinpath(exe))
        return path

    def create_scripts(path):
        os.mkdir(path)
        for exe in script_exes(ver):
            touch(path.joinpath(exe))

    for v in versions:
        ver = version.parse(v)
        version_path = create_pythons(versions_dir.joinpath(v))
        create_scripts(version_path.joinpath('Scripts'))
    if global_ver is not None:
        with open(Path(pyenv_path, "version"), "w") as f:
            print(global_ver, file=f)
    if local_ver is not None:
        with open(Path(local_path, ".python-version"), "w") as f:
            print(local_ver, file=f)


class PyenvContext:
    def __init__(self, pyenv, pyenv_path, local_path):
        self.pyenv = pyenv
        self.pyenv_path = pyenv_path
        self.local_path = local_path


def run_pyenv_test(settings, commands):
    with tempfile.TemporaryDirectory() as tmp_path:
        settings['pyenv_path'] = pyenv_path = Path(tmp_path, 'pyenv')
        settings['local_path'] = local_path = Path(tmp_path, 'local')
        os.mkdir(pyenv_path)
        os.mkdir(local_path)
        pyenv_setup(settings)
        with working_directory(local_path):
            bat = Path(pyenv_path, r'bin\pyenv.bat')

            def pyenv(pyenv_args=None):
                args = ['cmd', '/d', '/c', f'call {bat}']
                if pyenv_args is not None:
                    if isinstance(pyenv_args, list):
                        args = args + pyenv_args
                    else:
                        args.append(pyenv_args)
                result = subprocess.run(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stderr = str(result.stderr, "utf-8").strip()
                if stderr != "":
                    print(stderr)
                # \x0c: generated by cls in cmd AutoRun
                stdout = str(result.stdout, "utf-8").strip("\r\n\x0c")
                return stdout

            context = PyenvContext(pyenv, pyenv_path, local_path)
            commands(context)


def not_installed_output(ver):
    return (f"pyenv specific python requisite didn't meet. "
            f"Project is using different version of python.\r\n"
            f"Install python '{ver}' by typing: 'pyenv install {ver}'")


def local_python_versions(path):
    with open(Path(path, '.python-version'), mode='r') as f:
        return f.read().strip()
