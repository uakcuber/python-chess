import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix __init__ and API polling properties
# We need to make sure the inside of draw uses self. properties.
# Rather than string replace, let's just write the exact main.py contents.
