import csv
import sys
import requests
import pprint

from langsci.langscipressorg_webcrawler import (
    get_soup,
    get_publication_date,
    get_citeinfo,
    get_ISBN_digital,
    get_ISBN_hardcover,
    get_title_subtitle,
    get_biosketches,
    biosketches2names,
    get_blurb
)





fields = """Print_ISBN
Title
Subtitle
Series_Title
Creator_1_Role
Creator_1_First_Name
Creator_1_Last_Name
Creator_1_Affiliation
Creator_1_ORCID
Creator_2_Role
Creator_2_First_Name
Creator_2_Last_Name
Creator_2_Affiliation
Creator_2_ORCID
Creator_3_Role
Creator_3_First_Name
Creator_3_Last_Name
Creator_3_Affiliation
Creator_3_ORCID
Creator_4_Role
Creator_4_First_Name
Creator_4_Last_Name
Creator_4_Affiliation
Creator_5_Role
Creator_5_First_Name
Creator_5_Last_Name
Creator_5_Affiliation
Creator_6_Role
Creator_6_First_Name
Creator_6_Last_Name
Creator_6_Affiliation
Creator_7_Role
Creator_7_First_Name
Creator_7_Last_Name
Creator_7_Affiliation
Creator_8_Role
Creator_8_First_Name
Creator_8_Last_Name
Creator_8_Affiliation
Creator_9_Role
Creator_9_First_Name
Creator_9_Last_Name
Creator_9_Affiliation
FUNDER_ID
FUNDER_NAME
PROGRAM_NAME
PROJECT_NAME
PROJECT_ACRONNYM
GRANT_NUMBER
Description
PRINT_BINDING
EUR_Hardback_Price
USD_Hardback_Price
EUR_Paperback
USD_Paperback_Price
Publisher_Name
Publication_Date
Place_of_Publication
Licence_Boolean
Licence_Type
Primary_Subject
BISAC
BIC
Manual_Keywords
Level
DOI
Pagination
OA_ISBN""".split()


rows = []
book_IDs = sys.argv[1:]
for book_ID in book_IDs:
    soup = get_soup(book_ID)
    citegroups = get_citeinfo(soup)
    biosketches = get_biosketches(soup)
    if citegroups is None:
        sys.exit()

    title, subtitle = get_title_subtitle(citegroups)
    series = citegroups["series"]
    description = get_blurb(soup)
    creatorlist = biosketches2names(biosketches)
    role = "author"
    if citegroups["ed"]:
        role = "editor"
    isbn_hardcover = get_ISBN_hardcover(soup, drophyphens=False)
    isbn_digital = get_ISBN_digital(soup, drophyphens=False)

    d = {k:'' for k in fields}
    d["Place_of_Publication"] = "Berlin"
    d["Publisher_Name"] = "Language Science Press"
    d["Level"] = "Both"
    d["Licence_Type"] = "CC-BY"
    d["Licence_Boolean"] = True
    d["PRINT_BINDING"] = "Hardback"
    d["Primary_Subject"] = "Linguistics"
    d["BISAC"] = "LAN9000"
    d["DOI"] = citegroups['doi']
    d["OA_ISBN"]=isbn_digital
    d["Print_ISBN"]=isbn_hardcover
    d["Description"]=description
    d["Title"]=title
    d["Subtitle"]=subtitle
    d["Series_Title"]=citegroups["series"]

    creator_ID = 1
    for creator in creatorlist:
        d[f"Creator_{creator_ID}_First_Name"] = creator[0]
        d[f"Creator_{creator_ID}_Last_Name"] = creator[1]
        d[f"Creator_{creator_ID}_Role"] = role
        creator_ID += 1
    row = [d[key] for key in fields]
    rows.append(row)


with open('ku.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(fields)
    for row in rows:
        writer.writerow(row)




