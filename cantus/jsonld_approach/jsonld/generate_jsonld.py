"""
Generates a compact JSON-LD file from the reconciled CSV file.
"""

import pandas as pd
import json
import re

# add the path to your reconciled csv to produce the compact jsonld.
# to change the context by :
#       - replace the '@context' key below with another context in the url
#       - make changes to the file 'context.jsonld' and make sure to push the 
#         changes on the appropriate branch (make sure the link below match where you host the context)
df = pd.read_csv("./cantus/data/reconciled/cantus-csv.csv")

json_data = df.to_json(orient='records')
parsed_json = json.loads(json_data)


def handle_rec_col(work,key):
    """
    Handles the json-ld-ification of columns that have been reconciled.
    Expects there to be a column with the same name as the key, and a column with the key + '_@id'.
    Returns the value of the key if it is not reconciled, or a dictionary with the @id and name if it is.
    """
    val = work.pop(key)
    wID = work.pop(f'{key}_@id')
    if val is None:
        return None
    if re.match(r"^[Q]\d+", wID ): #if cell was reconciled with wikidata
        # work["@context"].append({key:f"wdt:{name_wID}"}) # overwrite context
        return {"@id":f"wd:{wID}",
                "name":val}
        
    if val[:8]=="https://" : #if cell was reconciled with another source
        return {"@id": val}
    else: #cell is value
        # work["@context"].append({key:f"wdt:{wID}"}) # overwrite context
        return val


def create_json_compact(js):
    """
    Takes the CSV parsed as JSON and creates a compact JSON-LD file.
    The @context is set to the one in the context.jsonld file.
    """
    for work in js:

        work["@context"] = "https://raw.githubusercontent.com/ddmal/linkedmusic-datalake/main/cantus/jsonld_approach/jsonld/context.jsonld"
        work["@id"] = f"chant:{work.pop('chant_id')}" #the @id of each document should be the link to the chant in its database
        work["@type"] = "wd:Q23072435" #chant

        work['database'] = 'cantusdb:'
        # work["P1922"] = work.pop("incipit")

        work["genre"] = handle_rec_col(work,"genre")
        work["mode"] = handle_rec_col(work, "mode")
        work["service"] = handle_rec_col(work, "service")

        # work["Q4484726"] = work.pop("finalis") #wikidata Final is closest term to finalis

        work["cantus_id"] = f"https://cantusindex.org/id/{work.pop('cantus_id')}"

  
     
    # Print the nested list of dictionaries
    return json.dumps(js, indent=4)



with open('compact.jsonld', 'w', encoding="utf-8") as json_file:
    json_file.write(create_json_compact(parsed_json))
