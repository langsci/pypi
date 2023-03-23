try:
    from langscipressorg_webcrawler import get_soup, get_citeinfo
    from catalogmetadata import METALANGUAGE, ONE_LANGUAGE_BOOKS, LICENSES, SUPERSEDED
except ImportError:
    from langsci.langscipressorg_webcrawler import get_soup, get_citeinfo
    from langsci.catalogmetadata import METALANGUAGE, ONE_LANGUAGE_BOOKS, LICENSES, SUPERSEDED

def second_comma_to_ampersand(s):
    if not " & " in s:
        return s
    print(s)
    non_last_creator_string, last_creator = s.split(" & ")
    non_last_creator_list = non_last_creator_string.split(", ")
    result = ""
    comma_flag = True
    for creator_name_part in non_last_creator_list:
        result += creator_name_part
        if comma_flag:
            result += ", "
            comma_flag = False
        else:
            result += " & "
            comma_flag = True
    result += last_creator
    return result


fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber creators title year".split()
csvstrings = ["\t".join(fields)]

for ID in range(16,400):
    soup = get_soup(ID)
    citegroups = get_citeinfo(soup)
    if citegroups is None:
        continue
    creators = citegroups["creators"].replace("&nbsp;&nbsp;", "&")
    creators = second_comma_to_ampersand(creators)
    fields = [str(ID),
                citegroups["doi"] or '',
                citegroups["ed"] or '',
                METALANGUAGE.get(ID, "eng"),
                ONE_LANGUAGE_BOOKS.get(ID,['','',''])[1],
                LICENSES.get(ID, "CC-BY  4.0"),
                str(ID in SUPERSEDED),
                '',
                citegroups["series"],
                citegroups["seriesnumber"],
                creators,
                citegroups["title"].strip(),
                citegroups["year"].strip()
                ]
    csvstrings.append("\t".join(fields))

with open("catalog.csv", "w") as csvout:
    csvout.write("\n".join(csvstrings))
