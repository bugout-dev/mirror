from setuptools import find_packages, setup

VERSION = '0.1.0'

setup(
    name='dungineers-mirror',
    version=VERSION,
    packages=find_packages(),
    install_requires=[
        'requests',
        'tqdm',
    ],
    description='mirror: Data analysis for software projects',
    author='Neeraj Kashyap',
    author_email='neeraj@simiotics.com',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
    ],
    url='https://github.com/simiotics/mirror',
    entry_points={
        'console_scripts': [
            'mirror = mirror.cli:main'
        ]
    }
)
