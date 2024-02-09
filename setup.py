from setuptools import setup

setup(
    name='cbpi4-sqldb',
    version='0.0.1',
    description='Add support, to log sensor data to a MySQL Database',
    author='MiracelVip ',
    author_email='',
    url='https://github.com/MiracelVip/cbpi4-sqldb',
    include_package_data=True,
    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst', '*.yaml'],
        'cbpi4-sqldb': ['*', '*.txt', '*.rst', '*.yaml']
    },
    packages=['cbpi4-sqldb'],
    install_requires=[
        'aiomysql',
    ],
) 