from setuptools import setup, Command, find_packages, errors
from shutil import rmtree
import os
import sys

# Package meta-data.
NAME = 'meeshkan'
DESCRIPTION = 'Reverse engineer services with style'
URL = 'http://github.com/meeshkan/meeshkan'
EMAIL = 'dev@meeshkan.com'
AUTHOR = 'Meeshkan Dev Team'
REQUIRES_PYTHON = '>=3.6.0'

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

REQUIRED = [
    'click',
    'pyyaml',
    'jsonschema',
    'typing-extensions',
    'openapi-typed',
    'typeguard>=2.7.0',
    'genson',
    'http-types>=0.0.3'
]

DEV = [
    'pytest',
    'pylint',
    'setuptools',
    'twine',
    'wheel',
    'pytest-watch',
    'pytest-testmon',
    'pyhamcrest'
]

VERSION = '0.2.0'

ENTRY_POINTS = ['meeshkan = meeshkan.__main__:cli']

# Optional packages
EXTRAS = {'dev': DEV}


class SetupCommand(Command):
    """Base class for setup.py commands with no arguments"""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def rmdir_if_exists(self, directory):
        self.status("Deleting {}".format(directory))
        rmtree(directory, ignore_errors=True)


def build():
    return os.system(
        "{executable} setup.py sdist bdist_wheel --universal".format(executable=sys.executable))


def type_check():
    os.system("pyright --lib")


class BuildDistCommand(SetupCommand):
    """Support setup.py upload."""
    description = "Build the package."

    def run(self):
        self.status("Removing previous builds...")
        self.rmdir_if_exists(os.path.join(here, 'dist'))

        self.status("Building Source and Wheel (universal) distribution...")
        build()
        sys.exit()


class TypeCheckCommand(SetupCommand):
    """Run type-checking."""
    description = "Run type-checking."

    def run(self):
        type_check()
        sys.exit()


class TestCommand(SetupCommand):
    """Support setup.py test."""
    description = "Run local test if they exist"

    def run(self):
        os.system("pytest")
        sys.exit()


class UploadCommand(SetupCommand):
    """Support setup.py upload."""
    description = "Build and publish the package."

    def run(self):

        self.status("Removing previous builds...")
        self.rmdir_if_exists(os.path.join(here, 'dist'))

        self.status("Building Source and Wheel (universal) distribution...")
        exit_code = build()
        if exit_code != 0:
            raise errors.DistutilsError("Build failed.")
        self.status("Uploading the package to PyPI via Twine...")
        os.system("twine upload dist/*")

        self.status("Pushing git tags...")
        os.system("git tag v{about}".format(about=VERSION))
        os.system("git push --tags")

        sys.exit()


setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=long_description,
      long_description_content_type='text/markdown',
      url=URL,
      author=AUTHOR,
      author_email=EMAIL,
      python_requires=REQUIRES_PYTHON,
      license='MIT',
      packages=find_packages(exclude=('tests',)),
      include_package_data=True,
      install_requires=REQUIRED,
      extras_require=EXTRAS,
      classifiers=[
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
      ],
      zip_safe=False,
      entry_points={'console_scripts': ENTRY_POINTS},
      cmdclass={'dist': BuildDistCommand,
                'upload': UploadCommand,
                'test': TestCommand,
                'typecheck': TypeCheckCommand}
      )
