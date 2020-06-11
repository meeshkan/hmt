import os
import sys
from distutils import errors
from shutil import rmtree

from setuptools import Command, find_packages, setup

# Package meta-data.
NAME = "hmt"
DESCRIPTION = "Reverse engineer services with style"
URL = "http://github.com/hmt/hmt"
EMAIL = "dev@hmt.com"
AUTHOR = "Meeshkan Dev Team"
REQUIRES_PYTHON = ">=3.6.0"

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

REQUIRED = [
    "click==7.0",
    "lenses",
    "pyyaml",
    "jsonschema",
    'dataclasses;python_version<"3.7"',  # for 3.6, as it ships with 3.7
    "faker",
    "requests",
    "typing-extensions",
    "openapi-typed_2>=0.0.4",
    "typeguard>=2.7.0",
    "genson",
    "http-types>=0.0.15,<0.1.0",
    # kafka
    "faust",
    # mock
    "tornado==5.1.1",
    "urllib3==1.25.6",
    "meeshkan-daemonocle",
    # tutorial
    "clint",
    "pyfiglet",
    "progress",
    "psutil>=5.6.3",
    "jsonpath-rw>=1.4.0",
]

BUNDLES = {}

# Requirements of all bundles
BUNDLE_REQUIREMENTS = [dep for _, bundle_dep in BUNDLES.items() for dep in bundle_dep]

DEV = BUNDLE_REQUIREMENTS + [
    "black==19.10b0",
    "flake8",
    "isort",
    "mypy",
    "pre-commit",
    "pyhamcrest",
    "pylint",
    "pytest>=5.4.1",
    "pytest-asyncio",
    "pytest-testmon",
    "pytest-tornado",
    "pytest-watch",
    "requests-mock",
    "setuptools",
    "twine",
    "wheel",
]

VERSION = "0.3.2"

ENTRY_POINTS = ["hmt = hmt.__main__:cli"]

EXTRAS = dict(**BUNDLES, dev=DEV)


def run_sys_command(cmd, error_msg):
    """Run command in os.system(), raise if exit_code non-zero.

    Arguments:
        cmd {[type]} -- Command to run. For example: "pytest"
        error_msg {[type]} -- Error message to raise at failure

    Raises:
        errors.DistutilsError: Exited with non-zero exit code.
    """
    exit_code = os.system(cmd)
    if exit_code != 0:
        raise errors.DistutilsError(error_msg)


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
        print("\033[1m{0}\033[0m".format(s))

    def rmdir_if_exists(self, directory):
        self.status("Deleting {}".format(directory))
        rmtree(directory, ignore_errors=True)


BUILD_COMMAND = "{executable} setup.py sdist bdist_wheel --universal".format(
    executable=sys.executable
)

TYPE_CHECK_COMMAND = "pyright --lib"

TEST_COMMAND = "pytest"

LINT_COMMAND = "flake8 --exclude .git,.venv,__pycache__,build,dist"

PRECOMMIT_COMMAND = "pre-commit run --all-files"


def build():
    run_sys_command(BUILD_COMMAND, "Build failed")


def type_check():
    run_sys_command(TYPE_CHECK_COMMAND, "Type-checking failed")


def run_tests():
    run_sys_command(TEST_COMMAND, "Tests failed")


def check_style():
    run_sys_command(LINT_COMMAND, "Checking style failed")


def enforce_formatting():
    run_sys_command(PRECOMMIT_COMMAND, "Formatting with precommit failed")


def check_formatting():
    run_sys_command(PRECOMMIT_COMMAND, "Formatting with precommit failed")


class BuildDistCommand(SetupCommand):
    """Support setup.py upload."""

    description = "Build the package."

    def run(self):
        self.status("Removing previous builds...")
        self.rmdir_if_exists(os.path.join(here, "dist"))
        self.status("Building Source and Wheel (universal) distribution...")
        build()


class FormatCommand(SetupCommand):
    """Enforce formatting."""

    description = "Enforce formatting."

    def run(self):
        enforce_formatting()


class TypeCheckCommand(SetupCommand):
    """Run type-checking."""

    description = "Run type-checking."

    def run(self):
        type_check()


class TestCommand(SetupCommand):
    """Support setup.py test."""

    description = "Run tests, formatting, type-checks, and linting"

    def run(self):
        self.status("Checking types...")
        type_check()

        self.status("Running pytest...")
        run_tests()


class UploadCommand(SetupCommand):
    """Support setup.py upload."""

    description = "Build and publish the package."

    def run(self):

        self.status("Removing previous builds...")
        self.rmdir_if_exists(os.path.join(here, "dist"))

        self.status("Building Source and Wheel (universal) distribution...")
        build()

        self.status("Uploading the package to PyPI via Twine...")
        os.system("twine upload dist/*")

        self.status("Pushing git tags...")
        os.system("git tag v{about}".format(about=VERSION))
        os.system("git push --tags")

        sys.exit()


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    license="MIT",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    zip_safe=False,
    entry_points={"console_scripts": ENTRY_POINTS},
    cmdclass={
        "dist": BuildDistCommand,
        "format": FormatCommand,
        "upload": UploadCommand,
        "test": TestCommand,
        "typecheck": TypeCheckCommand,
    },
)
