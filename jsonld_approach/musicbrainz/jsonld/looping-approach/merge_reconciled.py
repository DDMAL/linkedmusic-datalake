import json
import pandas as pd

# Load the CSV data into a Pandas DataFrame
id_table = pd.read_csv('extracted_ids.csv')
id_table['sameAs'] = "wd:"+id_table['sameAs'].str.extract(r'(Q\d+)$')

with open('../../data/initial_compact.jsonld', 'r') as f:
    data = json.load(f)

def add_context(data):
    for i in data:
        i["@context"] = [i["@context"],"https://raw.githubusercontent.com/malajvan/linkedmusic-datalake/main/musicbrainz/jsonld/looping-approach/context.jsonld"]
        i["database"] = "https://musicbrainz.org/"
def merge_ids(data, id_table):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'genre':
                genres = data['genre']
                fin_gen = []
                for i in genres:
                    matching_rows = id_table[id_table['@id'] == i]
                    # print('sam',matching_rows['sameAs'].values[0],'nbbame',matching_rows['name'].values[0])
                    if not matching_rows.empty:
                        sameAs = matching_rows['sameAs'].values[0] if not pd.isna(matching_rows['sameAs'].values[0]) else i

                        fin_gen.append( {'@id': sameAs,
                                            'name': matching_rows['name'].values[0]})
                data['genre'] = fin_gen
           
            if key == '@id':
                match = id_table[id_table['@id'] == data['@id']]['sameAs']
                if not match.empty:
                    data['@id'] = match.values[0] if not pd.isna(match.values[0]) else data['@id']
            if key == 'contentUrl':
                data['contentUrl'] = {"@id":"https:" + data['contentUrl']}
            else:
                # Recursively call merge_ids for nested dictionaries
                merge_ids(value, id_table)
    elif isinstance(data, list):
        # Recursively call merge_ids for elements in the list
        for i, item in enumerate(data):
            data[i] = merge_ids(item, id_table)
    return data

# Call merge_ids with the loaded data and id_table
output = merge_ids(data, id_table)
add_context(output)
# print(output)
# Save the modified data to a JSON file
with open('compact.jsonld', 'w') as json_file:
    json.dump(output, json_file, indent=2)

print('JSON file created with @id values.')
