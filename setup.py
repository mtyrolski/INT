from setuptools import setup, find_packages

setup(name='int_environment',
      version='0.1.0',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'gym>=0.26.2', 'torch>=2.0.0,!=2.0.1', 'torch-geometric>=2.3.1',
      ],
      extras_require={
      }
)