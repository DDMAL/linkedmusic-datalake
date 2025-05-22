# Key

1. Go to column `https://rism.online/api/v1#hasKeyMode` and go to `Edit column > Add column based on this column`, leave the GREL expression as value and name the new column `temp key`.
2. In the new column `temp key` go to `Edit cells > Transform...`, use the jython/python code: 

```
import re 
if re.match("\\d", value):
 return None 
key = value[0]
qual = "Major" 
if key != key.upper():
 key = key.upper()
 qual = "minor" 
if "|" in value: 
 if value[2] == "b":
  key += "-flat" 
 else:
  key += "-sharp" 
return key + " " + qual
```

3. Reconcile the column against type `tonality` (Q192822), and then go to `Reconcile > Actions > Match each cell to its best candidate`.
4. In the same column go to `Reconcile > Add columns with URLs of matched entities`, name the new column of URLs to be `http://www.wikidata.org/prop/direct/P826`.
5. Remove the column `temp key`.