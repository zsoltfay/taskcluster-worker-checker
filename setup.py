from setuptools import setup, find_packages
from client import main

requirements = open("requirements.txt").readlines()

setup(
    name='tc_worker_checker',
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)


main()
