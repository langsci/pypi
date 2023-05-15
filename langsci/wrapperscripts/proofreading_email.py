import PyPDF2
import re

try:
  from langscipressorg_webcrawler import get_blurb, get_soup, get_publication_date, get_citeinfo, get_ISBN_digital, get_biosketches, get_title_subtitle, biosketches2names
except ImportError:
  from langsci.langscipressorg_webcrawler import get_blurb, get_soup, get_publication_date, get_citeinfo, get_ISBN_digital, get_biosketches, get_title_subtitle, biosketches2names



with open("localmetadata.tex") as localmetadata:
    content = localmetadata.read()
    ID = re.search(r"\\lsID\}\{([0-9]+)\}", content).group(1)

soup = get_soup(ID)
citeinfo = get_citeinfo(soup)
title = citeinfo['title'].strip()
edited = citeinfo['ed'] or ""
creators = citeinfo['creators']
blurb = get_blurb(soup)

pdf = PyPDF2.PdfFileReader(open('main.pdf', 'rb'))
number_of_pages = pdf.numPages

with open("main.toc") as tocfile:
    content = tocfile.read()
    chapters = re.findall(r"numberline \{[0-9]+}*([A-Z].*?)\}",content)

number_of_chapters = len(chapters)
toc = "\n".join([f"{i+1} {ch}" for i, ch in enumerate(chapters)])


template = f"""Dear proofreader,
you are registered with Language Science Press as a proofreader. The
next book is about to reach proofreading stage. As you know, Language
Science Press depends on the community to help in the creation of our
books. We would therefore like to ask you if you could proofread one or
several chapters of the following volume:

{title}
    {edited} by {creators}

A description can be found on
https://langsci-press.org/catalog/book/{ID}
and below.

This book consists of {number_of_chapters} chapters with altogether {number_of_pages} pages. We would aim at having the proofreading completed within 4 weeks.

As always, proofreaders are acknowledged in the colophon of books and
also in our Hall of Fame (http://langsci-press.org/halloffame).

Please let us know whether you would find some time for proofreading
within the next 4 weeks, and if yes how many pages you would be willing
to take on.

Best wishes
Sebastian

Synopsis
====================

{blurb}

Table of contents
====================

{toc}
"""

print(template)
