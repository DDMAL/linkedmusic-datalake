import json

raw = json.loads(open("data/initial_compact.jsonld",'r').read())

cols = ['recordLabel', 'image', '@type', '@context', 'releaseOf', 'name', 'track', 'musicReleaseFormat', 'hasReleaseRegion', 'creditedTo', 'catalogNumber', 'sameAs', '@id', 'inLanguage', 'duration', 'gtin14', 'genre', 'producer']

release_key=[]
for re in raw:
    if 'releaseOf' in re.keys():
        for k in list(re['releaseOf'].keys()):
            if k not in release_key:
                release_key.append(k)

print(release_key)