import json
import generate_naive_json

#generate initial naive json
generate_naive_json.generate_naive_json()

doc = json.loads(open('naive.json',"r").read())


#note that we did not reconcile the_session cells so we won't need to handle_rec_cols

for rec in doc:
    rec['@id'] = f"tunes:{rec.pop('tune_id')}"
    rec['@type'] = "wd:Q2188189" #musical_work
    rec['@context'] = "https://raw.githubusercontent.com/malajvan/linkedmusic-datalake/main/thesession/jsonld/context.json"
    rec['tunes_type'] = {"@id":f"https://thesession.org/tunes/search?type={rec['tunes_type']}",
                         "name": rec['tunes_type']}
    

    # rec['P1476'] = rec.pop('tunes_name')
    
    rec['database'] = 'thesession:'
    try:
        rec['alias'] = rec.pop('aliases_alias')
    except KeyError:
        pass
    

    # rec['P2550'] = rec.pop('recordings')
    for r in rec['recordings']:
        r['@id'] = f"thesession:recordings/{r.pop('recordings_id')}"
        r['@type'] = "wd:Q3302947" #
        try:
            r['artist'] = r.pop('recordings_artist')
            r['recording'] = r.pop('recordings_recording')
            r['track'] = r.pop('recordings_track') # ignoring recordings number
        except KeyError:
            pass
        del r['recordings_number']
    try:
        rec['settings'] = rec.pop('tune_settings')
        for s in rec['settings']:
            s['@id'] = f"https://thesession.org/tunes/{rec['@id'].split(':')[1]}#setting{s.pop('tunes_setting_id')}"
            s['@type'] = "wd:Q113899068"
           
            s['meter'] = s.pop('tunes_meter')
            s['mode'] = s.pop('tunes_mode')
            s['date'] = s.pop("tunes_date").replace(' ','T')
            s['username'] = s.pop('tunes_username')

    except KeyError:
        pass    
pretty_json = json.dumps(doc, indent=4)
with open('compact.jsonld', 'w') as json_file:
    json_file.write(pretty_json)
