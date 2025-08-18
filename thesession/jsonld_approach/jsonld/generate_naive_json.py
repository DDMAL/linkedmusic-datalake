import pandas as pd
import json

def generate_naive_json():
    df = pd.read_csv('../flattening/final_merged.csv')
    float_columns = df.select_dtypes(include=['float']).columns

    # Convert float columns to int using pd.Int64Dtype()
    df[float_columns] = df[float_columns].astype(pd.Int64Dtype(), errors='ignore')



    json_data = df.to_json(orient='records')
    parsed_json = json.loads(json_data)
    cleaned_json = [{k: v for k, v in record.items() if v is not None} for record in parsed_json]
    pretty_json = json.dumps(cleaned_json, indent=4)


    # with open('naive_json.json', 'w') as json_file:
    #     json_file.write(pretty_json)


    def group_index(names, record):
        rec = {}
        
        for name in names:
            l = []

            for key, value in record.items():
                parts = key.split('_')
                
                # Check if the key matches the "name_..._#" pattern
                if parts[-1].isdigit() and parts[0] == name:
                    index = parts[-1]
                    found = False

                    # Check if the index already exists in the list
                    for s in l:
                        if list(s)[0].split('_')[-1] == index:
                            s[key] = value
                            found = True
                            break
                    
                    # If the index doesn't exist, create a new dictionary
                    if not found:
                        l.append({key: value})
                    
                # If the key isn't an indexed name, add it to the result directly
                elif not (parts[-1].isdigit() and parts[0] in names):
                    rec[key] = value

            # Add the list to the result under the name key
            rec[name] = l
        
        return rec


    def clean_up_indexes_recursive(obj):
        if isinstance(obj, dict):
            cleaned_obj = {}
            for key, value in obj.items():
                parts = key.rsplit('_', 1)
                cleaned_key = parts[0] if len(parts) == 2 and parts[1].isdigit() else key
                cleaned_value = clean_up_indexes_recursive(value)
                cleaned_obj[cleaned_key] = cleaned_value
            return cleaned_obj
        elif isinstance(obj, list):
            cleaned_list = []
            for item in obj:
                cleaned_item = clean_up_indexes_recursive(item)
                cleaned_list.append(cleaned_item)
            return cleaned_list
        else:
            return obj


    final_json=[]
    names = ['tunes', 'recordings']
    for record in cleaned_json:
        grouped = group_index(names, record)
        clean_index = clean_up_indexes_recursive(grouped)
        clean_index['tune_settings'] = clean_index.pop('tunes') 
        final_json.append(clean_index) #grouping indexed as a nested json doc/list



    pretty_json = json.dumps(final_json, indent=4)
    with open('naive.json', 'w') as json_file:
        json_file.write(pretty_json)






