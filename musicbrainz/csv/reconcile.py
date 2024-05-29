import pandas as pd
import requests
import os
import re

# Load the CSV file
DIRNAME = os.path.dirname(__file__)
FILENAME = os.path.join(DIRNAME, 'data', 'out.csv')
data = pd.read_csv(FILENAME)
OUTNAME = os.path.join(DIRNAME, 'data', 'reconciled.csv')
OUTDATA = pd.DataFrame()

# Function to reconcile IDs with MusicBrainz
def reconcile_musicbrainz(id, entity_type='recording'):
    url = f"https://musicbrainz.org/{entity_type}/{id}"
    response = requests.get(url)
    if response.status_code == 200:
        return url
    else:
        return None

# Function to reconcile using Wikidata API
def reconcile_wikidata(query, type='item'):
    url = f"https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbsearchentities',
        'search': query,
        'language': 'en',
        'format': 'json',
        'type': type
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get('search', [])
        if results:
            return results[0].get('concepturi')
    return None

def get_id_type(column : str):
    keywords = column.split("_")
    word = keywords[-2]
    word = re.sub(r'\d+', '', word)
    return word

# Reconcile names, titles, and genres using Wikidata
for col in data.columns:
    print(col)
    if col == 'title' :
        OUTDATA[f'{col}_wk_url'] = data[col].apply(lambda x: reconcile_wikidata(x, 'single') if pd.notna(x) else None)
    elif 'name' in col:
        OUTDATA[f'{col}_wk_url'] = data[col].apply(lambda x: reconcile_wikidata(x) if pd.notna(x) else None)
    elif col == 'id':
        OUTDATA['absolute_url'] = data[col].apply(lambda x: reconcile_musicbrainz(x))
    elif 'ids' in col:
        keyword = get_id_type(col)
        OUTDATA[f'{col}_musicbrainz_url'] = data[col].apply(lambda x: reconcile_musicbrainz(x, entity_type=keyword) if pd.notna(x) else None)
        print(keyword, OUTDATA[f'{col}_musicbrainz_url'])
    else:
        OUTDATA[col] = data[col]
        
OUTDATA.to_csv(OUTNAME, index=False)