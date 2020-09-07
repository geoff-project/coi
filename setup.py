#!/usr/bin/env python3
"""Setup script for shared_interfaces."""

from pathlib import Path
from setuptools import setup, find_namespace_packages

THISDIR = Path(__file__).parent.resolve()


def strip_quotes(string):
    """Check if a string is surrounded by consistent quotes."""
    is_quoted = string[0] == string[-1] in ('"', "'")
    if not is_quoted:
        raise ValueError(f'not a string: {string}')
    return string[1:-1]


def get_version():
    """Read the version number from the repository."""
    version = None
    path = THISDIR / 'cernml' / 'abc' / '__init__.py'
    with path.open() as infile:
        for line in infile:
            before, equals, after = line.partition('=')
            if equals and before.strip() == '__version__':
                version = strip_quotes(after.strip())
    if not version:
        raise ValueError(f'no version found in {infile.name}')
    return version


LONG_DESCRIPTION = """\
Common interfaces to use both reinforcement learning and numerical optimization
for problems of optimal control at DESY and CERN.
"""

setup(
    name='cernml-abc',
    version=get_version(),
    python_requires='>=3.6',
    packages=find_namespace_packages(include=('cernml', 'cernml.*')),
    install_requires=['gym >= 0.11'],
    zip_safe=True,
    author='Nico Madysa',
    author_email='nico.madysa@cern.ch',
    description='Common interfaces for RL/num. optimization at DESY and CERN',
    long_description=LONG_DESCRIPTION,
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
