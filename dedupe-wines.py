#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
import os

def dedupe_wines(input_file):
    try:
        with open(input_file, "r") as f:
            wines = json.load(f)
    except IOError:
        print("File not found: {}".format(input_file))
        sys.exit(1)
    except ValueError as e:  # json.JSONDecodeError doesn't exist in Python 2
        print("Invalid JSON: {}".format(e))
        sys.exit(1)

    print("Loaded {} wine entries".format(len(wines)))

    seen_names = set()
    unique_wines = []

    for wine in wines:
        wine_name = None
        try:
            wine_name = wine.get("summary", {}).get("name")[:-4]
        except AttributeError:
            pass
        if wine_name and wine_name not in seen_names:
            seen_names.add(wine_name)
            unique_wines.append(wine)
        else:
            print("Duplicate found: {}".format(wine_name.encode('utf-8')))

    folder = os.path.dirname(input_file)
    basename = os.path.basename(input_file)
    output_file = os.path.join(folder, "dedupe-" + basename)

    # In Python 2, json.dump does NOT have ensure_ascii as a named parameter unless >=2.7.9, but it's safe for simple strings.
    with open(output_file, "w") as f:
        json.dump(unique_wines, f, indent=2)

    print("Duplicates removed.")
    print("Original: {} → Deduped: {}".format(len(wines), len(unique_wines)))
    print("Saved to: {}".format(output_file))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dedupe_wines.py <file.json>")
        sys.exit(1)
    dedupe_wines(sys.argv[1])
