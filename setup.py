import setuptools
from setuptools import setup
setup(
    name='proxcli',
    version='1.0',
    py_modules=['proxcli', 'proxmoxlib'],
    install_requires=[
        'proxmoxer',
        'beautifultable',
        'termcolor',
        'requests',
        'pyyaml',
        'typer',
        'colored',
        'rich'
    ],
    entry_points='''
        [console_scripts]
        proxcli=proxcli:app
    ''',
)