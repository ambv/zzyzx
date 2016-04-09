import ast
import os
import re
from setuptools import setup

current_dir = os.path.abspath(os.path.dirname(__file__))
ld_file = open(os.path.join(current_dir, 'README.rst'))
try:
    long_description = ld_file.read()
finally:
    ld_file.close()


_version_re = re.compile(r'__version__\s+=\s+(?P<version>.*)')


with open('zzyzx/__init__.py', 'rb') as f:
    version = _version_re.search(f.read().decode('utf-8')).group('version')
    version = str(ast.literal_eval(version))


setup(
    name='zzyzx',
    author='Łukasz Langa',
    author_email='lukasz@langa.pl',
    version=version,
    url='http://github.com/ambv/zzyzx',
    packages=['zzyzx'],
    package_data={
        '': ['*.txt', '*.rst'],
    },
    entry_points={
        'console_scripts': ['zzyzx=zzyzx.cli:main'],
    },
    description='A simple IMAP Notes backup tool.',
    long_description=long_description,
    zip_safe=False,
    platforms=['any'],
    install_requires=[
        'click',
    ],
    extras_require={
        'collation': ["PyICU"],
        'markdown': ["beautifulsoup4", "python-magic"],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
