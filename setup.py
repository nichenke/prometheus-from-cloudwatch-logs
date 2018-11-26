""" Build and packaging """

from setuptools import setup, find_packages

setup(name="cloudwatch_prom",
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"])
     )
