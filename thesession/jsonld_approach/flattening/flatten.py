"""
How to run: 
1. Put source csv files under the_session/flattening/data
2. Run script flatten.py
"""
import pandas as pd
from helper_functions import flatten_aliases, flatten_recordings, flatten_tunes

#create flattened file for aliases and tunes
flatten_aliases()
flatten_tunes()

# Define the file paths for each needed CSV file
csv_files = {
    #These are transformed
    'tunes': 'transformed/flatten_tunes.csv',
    'aliases': 'transformed/flatten_aliases.csv',
    'events': 'events.csv',
    'popularity': 'tune_popularity.csv', #Popularity doesn't need to be flattened
    'recordings': 'recordings.csv' #we will flatten recordings below

}

# Load each CSV file into a DataFrame
dfs = {}
for table_name, file_path in csv_files.items():
    df = pd.read_csv(f'data/{file_path}')
    df.columns = [table_name + '_' + col if col != 'tune_id' else col for col in df.columns] # add table name so each column for clarity and facilitate jsonld generation
    dfs[table_name] = df

dfs['tunes'] = dfs['tunes'].head(100) #choosing only the first 100 tunes for now

# Merge initial tables with foreign key relationships
merged_df = pd.merge(dfs['popularity'], dfs['tunes'], on='tune_id', how='right')
no_recording = pd.merge(merged_df, dfs['aliases'], on='tune_id', how='left')

# start merging recordings (unsure why it needs to be this complicated)
# TODO: cleanup recordings merging
merged_on=['tune_id']
with_recording = pd.merge(no_recording, dfs['recordings'], on='tune_id', how='left')

with_recording['index_suffix'] = with_recording.groupby(merged_on).cumcount() + 1

flatten_recordings(with_recording,merged_on)
pivot_table = pd.read_csv('data/transformed/flatten_recordings.csv')
final = pd.merge(no_recording, pivot_table, on="tune_id", how="left")
final = final.drop(['popularity_name','aliases_name'],axis=1)
final.to_csv("final_merged.csv",index=False)

print('done to final_merged.csv')