# CONLL-U to Pandas DataFrame

Turn CONLL-U documents into Pandas DataFrames.

## Install

```shell
pip install conll-df
```

## Usage

```python
from conll_df import conll_df
path = "path/to/f.conllu"
df = conll_df(path)
```

## Returns:

A Multiindexed DataFrame:

```

```

## Arguments:

| Name  | Type  | Description  |
|---|---|---|
| `path`  | `str`  | Path to CONLL-U file  |
| `add_gov`  | `bool`  | Create extra fields for governor word, lemma, POS and function  |
| `skip_morph`  | `bool`  | Enable if you'd like to skip the parsing of morphological and extra fields  |
| `v2`  | `bool`/`auto`  | CONLL-U version of file. By default, detect |
| `drop` | `list` | list of column names you don't need |
| `add_meta` | `bool` | add columns for sentence-level metadata |
| `categories` | `bool` | Convert columns to categorical format where possible |
| `file_index` | `bool` | Include filename in index levels |
| `kwargs`  | `dict` | additional arguments to pass to `pandas.read_csv()` |

## Where to from here?

```python
# get nominal subjects
df.f.str.contains('nsubj')
# groupby sentence
gb = df.groupby(level=['file', 's'])
```