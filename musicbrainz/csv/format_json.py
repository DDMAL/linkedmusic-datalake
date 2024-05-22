import json

def format() -> None:
    """
    Format the downloaded json file, which is not readable for python json library.
    """
    with open("test", 'r') as json_file:
        with open("json_init.json", 'w') as out:
            out.write("[")
            lines = json_file.readlines()
            last = lines[-1]
            for line in lines:
                if line is not last:
                    line += ","
                out.writelines(line)
            out.write("]")