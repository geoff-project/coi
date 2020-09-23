#!/usr/bin/env python3
"""Setup script for cernml-coi."""

from pathlib import Path
from setuptools import setup, find_namespace_packages

THISDIR = Path(__file__).parent.resolve()


def get_long_description() -> str:
    """Read the README into a string."""
    with (THISDIR / 'README.md').open('rt') as infile:
        return infile.read().strip()


def strip_quotes(string):
    """Check if a string is surrounded by consistent quotes."""
    is_quoted = string[0] == string[-1] in ('"', "'")
    if not is_quoted:
        raise ValueError(f'not a string: {string}')
    return string[1:-1]


def get_version():
    """Read the version number from the repository."""
    version = None
    path = THISDIR / 'cernml' / 'coi' / '__init__.py'
    with path.open() as infile:
        for line in infile:
            before, equals, after = line.partition('=')
            if equals and before.strip() == '__version__':
                version = strip_quotes(after.strip())
    if not version:
        raise ValueError(f'no version found in {infile.name}')
    return version


setup(
    name='cernml-coi',
    version=get_version(),
    python_requires='>=3.6',
    packages=find_namespace_packages(include=('cernml', 'cernml.*')),
    install_requires=[
        'gym >= 0.11',
        'numpy ~= 1.10',
    ],
    extras_require={
        'test': [
            'matplotlib ~= 3.0',
        ],
    },
    zip_safe=True,
    author='Nico Madysa',
    author_email='nico.madysa@cern.ch',
    description='Common optimization interfaces for RL/num. optimization',
    long_description=get_long_description(),
    license='Other/Proprietary License',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: Other/Proprietary License',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Physics',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
    ],
    url='https://github.com/cern-desy-acc-opt/shared-interfaces',
)
