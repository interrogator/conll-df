import pandas as pd

# UD 1.0
CONLL_COLUMNS = ['i', 'w', 'l', 'p', 'n', 'm', 'g', 'f', 'd', 'c']
# UD 2.0
CONLL_COLUMNS_V2 = ['i', 'w', 'l', 'x', 'p', 'm', 'g', 'f', 'e', 'o']

# possible morphological attributes
MORPH_ATTS = ['type',
              'animacy',
              'gender',
              'number'
              "Abbr",
              "Animacy",
              "Aspect",
              "Case",
              "Definite",
              "Degree",
              "Evident",
              "Foreign",
              "Gender",
              "Mood",
              "NumType",
              "Number",
              "Person",
              "Polarity",
              "Polite",
              "Poss",
              "PronType",
              "Reflex",
              "Tense",
              "VerbForm",
              "Voice",
              "Type"]

def _make_sent_csv(sentstring, fname, meta, splitter, i, skip_meta=False):
    """
    Take one CONLL-U sentence and add all metadata to each row

    Return: str (CSV data) and dict (sent level metadata)
    """
    fixed_lines = []
    raw_lines = sentstring.splitlines()
    for line in raw_lines:
        if not line:
            continue
        if line.startswith('#'):
            if not skip_meta:
                try:
                    k, v = line.lstrip('# ').split(splitter, 1)
                except ValueError:
                    k, v = line.lstrip('# ').split(splitter.strip(), 1)
                meta[k.lower().strip()] = v.strip()
        else:
            line = '%s\t%s\t%s' % (fname, i, line)
            fixed_lines.append(line)
    return '\n'.join(fixed_lines), meta

def _add_governors_to_df(df):
    """
    Add governor info to a DF. Increases memory usage quite a bit.
    """
    # save the original index
    i = df.index.get_level_values('i')
    # add g
    dfg = df.set_index('g', append=True)
    # remove i
    dfg = dfg.reset_index('i')
    dfg = df.loc[dfg.index]
    dfg = dfg[['w', 'l', 'p', 'f']]
    dfg['i'] = i
    dfg = dfg.set_index('i', append=True)
    dfg.index.names = ['file', 's', 'g', 'i']
    dfg = dfg.reset_index('g', drop=True)
    for c in list(dfg.columns):
        try:
            dfg[c] = dfg[c].cat.add_categories(['ROOT'])
        except (AttributeError, ValueError):
            pass
    dfg = dfg.fillna('ROOT')
    dfg.columns = ['gw', 'gl', 'gp', 'gf']
    dfg = df.join(dfg, how="inner")
    return dfg





def conll_df(path,
               corpus_name=False,
               corp_folder=False,
               v2="auto",
               skip_morph=False,
               skip_meta=False,
               add_gov=False,
               drop=['text', 'newdoc id'],
               file_index=True,
               categories=True,
               extra_fields='auto',
               drop_redundant=True,
               **kwargs):
    """
    Optimised CONLL-U reader for v2.0 data

    Args:
        path (str): the file to prepare

    Returns:
        pd.DataFrame: 2d array representation of file data

    """
    import os
    import re
    try:
        from io import StringIO
    except ImportError:
        from StringIO import StringIO
        
    splitter = ' = ' if v2 else '='

    with open(path, 'r') as fo:
        data = fo.read().strip('\n')

    if v2 == 'auto':
        v2 = 'sent_id = ' in data[:9999]

    fname = os.path.basename(path)

    # metadata that applies filewide
    # a little bonus for those with annual data
    basedict = {}
    if not skip_meta:
        year = re.search(r'[12][0-9][0-9][0-9]', fname)
        if year:
            basedict['year'] = year.group(0)

    sents = data.split('\n\n')
    sents_meta = [_make_sent_csv(sstring, fname, dict(basedict), splitter, i, skip_meta=skip_meta) \
                  for i, sstring in enumerate(sents, start=1)]
    sents, metadata = zip(*sents_meta)
    
    # make the sent df
    sents = '\n\n'.join(sents)
    sents = StringIO(sents)

    if v2:
        cols = ['file', 's'] + CONLL_COLUMNS_V2
    else:
        cols = ['file', 's'] + CONLL_COLUMNS

    df = pd.read_csv(sents, sep="\t", header=None, names=cols, quoting=kwargs.pop('quoting', 3),
                     index_col=[0, 1, 2], engine='c', na_filter=False, **kwargs)

    if v2 and not skip_morph:
        df['m'] = df['m'].fillna('')
        df['o'] = df['o'].fillna('')
        if extra_fields == 'auto':
            # evil line to get all possible keys in the final column
            extra_fields = list(df['o'].str.extractall(r'(?:^|\|)([^=]+?)=')[0].unique())
        cats = MORPH_ATTS + extra_fields
        if 'SpaceAfter' not in cats:
            cats.append('SpaceAfter')
        om = df['o'].str.cat(df['m'], sep='|').str.strip('|_')
        # this is a very slow list comp, but i can't think of a better way to do it.
        # the 'extractall' solution makes columns for not just the value, but the key...
        extra = [om.str.extract('%s=([^|$]+)' % cat.title(), expand=True) for cat in cats]
        extra = pd.concat(extra, axis=1)
        extra.columns = cats
        df = pd.concat([df, extra], axis=1)

    # make and join the meta df
    if not skip_meta:
        metadata = {i: d for i, d in enumerate(metadata, start=1)}
        metadata = pd.DataFrame(metadata).T
        metadata.index.name = 's'
        df = metadata.join(df, how='inner')

    # we never want these to show up as a dataframe column
    badcols = ['sent_id', 's', 'i', 'file']
    
    # if we aren't parsing morph and extra columns, we should at least keep them
    if not skip_morph:
        badcols += ['o', 'm']
    if drop:
        badcols = badcols + drop
    df = df.drop(badcols, axis=1, errors='ignore')

    # some evil code to handle conll-u files where g col could be a string
    if 'g' in df.columns:
        df['g'] = df['g'].fillna(0)
        if df['g'].dtype in [object, str]:
            df['g'] = df['g'].str.replace('_', '0').astype(int)
        df['g'] = df['g'].astype(int)
    df = df.fillna('_')

    # attempt to categorise data
    if categories:
        for c in list(df.columns):
            if c in ['g', 'date']:
                continue
            try:
                df[c] = df[c].astype('category')
            except:
                pass

    if add_gov:
        df = _add_governors_to_df(df)

    if not file_index:
        df.index = df.index.droplevel('file')

    if drop_redundant:
        empty_cols = []
        for c in df.columns:
            if len(df[c].unique()) == 1:
                empty_cols.append(c)
        df = df.drop(empty_cols, axis=1)

    #reorder columns so that important things are first
    firsts = CONLL_COLUMNS_V2 if v2 else CONLL_COLUMNS
    firsts = [i for i in firsts if i in list(df.columns)]
    lasts = [i for i in list(df.columns) if i not in firsts]
    df = df[firsts + lasts]

    return df
