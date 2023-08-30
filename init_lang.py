import json
import os

def replace_special_chars(value):
    """Replace special characters in a string or list of strings with their Unicode representation."""
    if isinstance(value, str):
        value = json.dumps(value).replace("\"", "")
        value = value.replace('\\\\', '\\')
        return value
    elif isinstance(value, list):
        return [replace_special_chars(item) for item in value]
    return value

def old_replace_special_chars(value):
    """Replace special characters in a string or list of strings with their Unicode representation."""
    if isinstance(value, str):
        # Convert special characters to Unicode and then replace double backslashes
        value = value.encode('unicode_escape').decode('utf-8')
        return value
    elif isinstance(value, list):
        return [replace_special_chars(item) for item in value]
    return value

# Set the file_name variable
file_name = './lang/nbcn.json'

# Open and read the file specified by file_name
with open(file_name, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Empty the "en" key
data["en"] = {}

# Copy items from "source" to "en", replacing special characters with Unicode
for key, value in data["source"].items():
    data["en"][key] = replace_special_chars(value)

# Rename the original file to <filename>_old.json
base, ext = os.path.splitext(file_name)
old_file_name = base + "_old" + ext
if os.path.exists(old_file_name):
    os.remove(old_file_name)
os.rename(file_name, old_file_name)

# Save the modified content back to the original file_name
with open(file_name, 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=4)
