import setuptools
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
    py_modules=['proxcli', 'proxmoxlib'],
    install_requires=[
        'beautifultable==1.1.0',
        'certifi==2023.7.22',
        'charset-normalizer==3.2.0',
        'click==8.1.6',
        'colored==2.2.3',
        'exceptiongroup==1.1.2',
        'idna==3.4',
        'iniconfig==2.0.0',
        'markdown-it-py==3.0.0',
        'mdurl==0.1.2',
        'packaging==23.1',
        'pluggy==1.2.0',
        'proxcli==1.0',
        'proxmoxer==2.0.1',
        'Pygments==2.15.1',
        'pytest==7.4.0',
        'PyYAML==6.0.1',
        'requests==2.31.0',
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
