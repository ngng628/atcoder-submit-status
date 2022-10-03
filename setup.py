from setuptools import find_packages, setup

import atcoder_submit_status.__about__ as version

with open('README.md', 'r') as fp:
    readme = fp.read()

setup(
    name=version.__package_name__,
    version='0.0.1',
    author=version.__author__,
    author_email=version.__email__,
    url=version.__url__,
    license=version.__license__,
    keywords="atcoder",
    description=version.__description__,
    long_description=readme,
    python_requires='>=3.6',
    install_requires=[name.rstrip() for name in open('requirements.txt').readlines()],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'acss = atcoder_submit_status.main:main',
        ],
    },
)