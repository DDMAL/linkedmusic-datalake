import pandas as pd
import requests

# Load the CSV file
file_path = 'out.csv'
data = pd.read_csv(file_path)

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

# Reconcile IDs
data['musicbrainz_url'] = data['id'].apply(lambda x: reconcile_musicbrainz(x))

# Reconcile names, titles, and genres using Wikidata
for col in ['title', 'genres1_name', 'genres2_name', 'genres3_name']:
    if col in data.columns:
        data[f'{col}_wikidata'] = data[col].apply(lambda x: reconcile_wikidata(x) if pd.notna(x) else None)
