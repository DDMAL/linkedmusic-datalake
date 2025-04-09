import csv
import pandas as pd

# Note: This script is ran AFTER SQL_query.py script and AFTER reconciliation.
# This script takes in a reconciled version of csv and:
#  1. Filter for only the columns we're interested in
#  2. Merge columns so that each row corresponds to a musical_work_id instead of file_id as previously
#     Each file is now belong to a musical work


df = pd.read_csv("../reconciled_WikiID.csv")
# get only the columns we're interested in
cols = ['musical_work_id','sacred_or_secular','source_id','contribution_id', "VIAF ID", "genre_style_@id","genre_style",'genre_type','genre_type_@id','url_to_file','contributor_role','contributor_role_@id','source_instantiation_portion','source_title', 'source_type','source_url', 'file_type','file_format','file_format_@id','musical_work_variant_titles','file_version',"contributor_name",'contributor_name_@id']
df2 = df[cols]


# df2['musical_work_id'] = df2['musical_work_id'].astype(int)


# # since the flattening process flattened the info related to files (file_formats, url_to_file, Last_Pitch), we merge on the other columns
# merge_on = ["musical_work_id",'musical_work_variant_titles','composer', 'genre_style','genre_type']

# df2['test_count'] = df2.groupby("musical_work_id").cumcount() + 1
# df2 = df2.pivot(index=merge_on, columns='test_count', values=['file_format','url_to_file', 'Last_Pitch_Class'])

# # Flatten the multi-index columns
# df2.columns = [f'{col[0]}_{col[1]}' for col in df2.columns]
# # now each columns represent a row, each row will have the 

# # Reset the index
# df2 = df2.reset_index()




df2.to_csv('./final_flattened.csv', index=False)
