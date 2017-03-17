from setuptools import setup

setup(name='conll_df',
      version='0.0.3',
      description='CONLL-U to Pandas DataFrame',
      url='http://github.com/interrogator/conll-df',
      packages=['conll_df'],
      author='Daniel McDonald',
      author_email="mcddjx@gmail.com",
      license='MIT',
      keywords=['corpus', 'linguistics', 'nlp', 'treebank', 'parsing', 'conll', 'ud'],
      install_requires=["pandas>=0.19.2"])
