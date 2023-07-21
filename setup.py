import setuptools
from setuptools import setup
setup(
    name='proxmox',
    version='1.0',
    py_modules=['proxmox', 'proxmoxlib'],
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
        proxmox=proxmox:app
    ''',
)