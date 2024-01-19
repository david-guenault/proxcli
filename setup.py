"""Setup proxcli"""
from setuptools import setup
setup(
    name='proxcli',
    version='1.0',
    author='David GUENAULT',
    author_email='david.guenault@gmail.com',
    maintainer_email='david.guenault@gmail.com',
    maintainer='David GUENAULT',
    license='Apache License Version 2.0',
    python_requires=">=3.6",
    py_modules=['proxcli', 'proxmoxlib', 'proxcli_exceptions', 'stack_config'],
    install_requires=[
        'beautifultable==1.1.0',
        # 'click==8.1.6',
        # 'colored==2.2.3',
        'proxcli==1.0',
        'proxmoxer==2.0.1',
        'requests==2.31.0',
        'requests-toolbelt==1.0.0',
        'termcolor==2.3.0',
        'typer==0.9.0',
        'typing_extensions==4.7.1',
        'wcwidth==0.2.6',
        'PyYAML==6.0.1',
        'rich==13.6.0'
    ],
    entry_points='''
        [console_scripts]
        proxcli=proxcli:app
    ''',
)
