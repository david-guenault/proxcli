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
    py_modules=['proxcli', 'proxmoxlib', 'proxcli_exceptions'],
    install_requires=[
        'ansible==8.5.0',
        'ansible-core==2.15.5',
        'beautifultable==1.1.0',
        'certifi==2023.7.22',
        'cffi==1.16.0',
        'charset-normalizer==3.2.0',
        'click==8.1.6',
        'colored==2.2.3',
        'cryptography==41.0.5',
        'exceptiongroup==1.1.2',
        'idna==3.4',
        'iniconfig==2.0.0',
        'Jinja2==3.1.2',
        'markdown-it-py==3.0.0',
        'MarkupSafe==2.1.3',
        'mdurl==0.1.2',
        'packaging==23.1',
        'pluggy==1.2.0',
        'proxcli==1.0',
        'proxmoxer==2.0.1',
        'pycparser==2.21',
        'Pygments==2.15.1',
        'pytest==7.4.0',
        'PyYAML==6.0.1',
        'requests==2.31.0',
        'requests-toolbelt==1.0.0',
        'resolvelib==1.0.1',
        'rich==13.4.2',
        'termcolor==2.3.0',
        'tomli==2.0.1',
        'typer==0.9.0',
        'typing_extensions==4.7.1',
        'urllib3==2.0.4',
        'wcwidth==0.2.6'
    ],
    entry_points='''
        [console_scripts]
        proxcli=proxcli:app
    ''',
)
