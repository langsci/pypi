#import  yaml
import sys
from datetime import date
#from xml.etree import ElementTree as ET
#from xml.sax.saxutils import escape
import xlrd
import xlsxwriter
from os.path import exists


try:
  from langscipressorg_webcrawler import get_blurb, get_soup, get_publication_date, get_citeinfo, get_ISBN_digital, get_biosketches, get_title_subtitle, biosketches2names, get_pdf
  from catalogmetadata import LICENSES, SERIES, METALANGUAGE
except ImportError:
  from langsci.langscipressorg_webcrawler import get_blurb, get_soup, get_publication_date, get_citeinfo, get_ISBN_digital, get_biosketches, get_title_subtitle, biosketches2names, get_pdf
  from langsci.catalogmetadata import LICENSES, SERIES, METALANGUAGE

today = date.today().strftime("%Y%m%d")

xlsx_headings = """publisher
ebook_title
pdf_isbn
epub_isbn
tracking_isbn
print_isbn
pub_prod_id
price
price_gbp
price_eur
price_jpy
price_cad
price_aud
price_nzd
discount_code
pub_year
orig_pub_year
author
author_nationality
electronic_rights
rights_exceptions
embargo_date
abridged_unabridged
description
subject
language
audience
author_notes
related_products
book_reviews
awards
marketing_statement
notes""".split()

workbook = xlrd.open_workbook("EBSCO_MDSS_v19.2_Master.xlsx")
sheets = workbook.sheets()
sheet = sheets[0]
workbook_out = xlsxwriter.Workbook('ebsco_langsci.xlsx')
newSheet = workbook_out.add_worksheet('eBooks')
for row in range(sheet.nrows):
    for col in range(sheet.ncols):
        newSheet.write(row, col, sheet.cell(row, col).value)

current_row = 3
for book_ID in range(16,400):
  soup = get_soup(book_ID)
  citegroups = get_citeinfo(soup)
  if citegroups is None:
    continue
  title, subtitle = get_title_subtitle(citegroups)

  series = citegroups["series"]

  publication_date = get_publication_date(soup)
  blurb = get_blurb(soup)
  isbn_digital =  get_ISBN_digital(soup)
  issn =  SERIES[citegroups["series"]]
  metalanguage = METALANGUAGE.get(book_ID, "eng")

  try:
    biosketches = get_biosketches(soup)
  except AttributeError:
    continue

  pdf_path = f"ebscopdfs/{isbn_digital}.pdf"
  if exists(pdf_path):
    pass
  else:
    get_pdf(soup, pdf_path)

  bisac = "LAN009000"
  #wgs = "9561"
  if series == "Translation and Multilingual Natural Language Processing":
      bisac = "LAN023000"

  #license = LICENSES.get(book_ID, "CC-BY")
  #license_url = "https://creativecommons.org/licenses/%s/4.0" % license[3:]
  #authorrolecode = "A01"
  #editorrolecode = "B01"

  #role = authorrolecode
  #if citegroups['ed']:
    #role = editorrolecode

  #creators = []
  creatorlist = biosketches2names(biosketches)

  #for i, creator in enumerate(creatorlist):
      #firstname = creator[0]
      #lastname = creator[1]
      #sketch = creator[2]
      ##creators.append(proquest_creator_template % (i+1, role, escape(firstname), escape(lastname), escape(sketch)))
  #creatorstring = "\n".join(creators)


  ebsco_creators = "; ".join([f"{n[1]}, {n[0]}" for n in creatorlist])

  ebsco_bios = "\n".join([n[2] for n in creatorlist])

  xlsx_d = {k:'' for k in xlsx_headings}
  xlsx_d['publisher'] = "Language Science Press"
  xlsx_d['ebook_title'] = title
  xlsx_d['pdf_isbn'] = isbn_digital
  #xlsx_d['epub_isbn'] = None
  #xlsx_d['tracking_isbn'] = None
  #xlsx_d['print_isbn'] = isbn_hardcover
  xlsx_d['pub_prod_id'] = book_ID
  xlsx_d['price'] = 0.01
  xlsx_d['pub_year'] = publication_date[:4]
  xlsx_d['author'] = ebsco_creators
  xlsx_d['electronic_rights'] = "WORLD"
  xlsx_d['description'] = blurb
  xlsx_d['subject'] = bisac
  xlsx_d['language'] = metalanguage
  xlsx_d['author_notes'] = ebsco_bios
  #xlsx_d['reviews'] = language
  #xlsx_d['awards'] = language
  xlsx_d['notes'] = "Open Access"

  for i, h in enumerate(xlsx_headings):
    v =  xlsx_d.get(h)
    newSheet.write(current_row, i, v)
    #print(current_row,i, v)
  current_row += 1

workbook_out.close()


