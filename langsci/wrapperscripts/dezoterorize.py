""" Tool for replacing zotero styled ciation keys with LangSci styled citation keys """

import re
import sys

filename = sys.argv[1]
bib = open(filename)
content = bib.read()

# step 1: "@article{nordhoff_unicode_2025," -> "@article{nordhoff2025,"

# match all "@type{contributor_topic_year," and group "@type{", "contributor", "_topic_" and "year,"
match = re.findall(r"(@[A-Z|a-z]+\{)(.*?)(_.*?_)(\d{4}|nodate),", content)
# delete the "_topic_" group
for typ, contributor, topic, year in match:
    old_key = f"{contributor}{topic}{year}"
    new_entry = f"{typ}{contributor}{year},"
    content = content.replace(f"{typ}{contributor}{topic}{year}", new_entry + f"\n\t ids={{{old_key}}}")

with open("new.bib", "w", encoding="utf8") as out:
    out.write(content)

# step 2: "@article{nordhoff2025," -> "@article{Nordhoff2025,"

# match all @typ{ContributorYear, and group "@typ" und "{ContributorYear,"
match2 = re.findall(r"(@[A-Z|a-z]+\{)([.*?]+\d*,)", content)

# replace first letter in "contributor" by its upper character
# and concatenate the new group with "typ{"
for typ, ContributorYear in match2:
    new_entry = f"{typ}{ContributorYear[0].upper() + ContributorYear[1:]}"
    content = content.replace(f"{typ}{ContributorYear}", new_entry)

# create new .bib file
with open(f"new{filename}", "w", encoding="utf8") as out:
    out.write(content)
