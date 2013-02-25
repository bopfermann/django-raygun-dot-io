from setuptools import setup, find_packages


description = 'Raygun.IO extensions for Django'
long_desc = open('README.rst').read()

setup(
    name='django-raygun-dot-io',
    version='0.0.1',
    install_requires=[
        'psutils'
    ],
    description=description,
    long_description=long_desc,
    author='Brandon Opfermann',
    author_email='bopfermann@wanttt.com',
    packages=find_packages()
)