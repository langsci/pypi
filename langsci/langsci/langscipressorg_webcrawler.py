import requests
import re
from bs4 import BeautifulSoup


CITEPATTERN = re.compile("(?P<creators>[^(]*)(?P<ed>\(eds?\.\))?\. (?P<year>[0-9]+)\. (?P<title>.*)\. \((?P<series>(.*)) (?P<seriesnumber>[0-9]*)\)\. Berlin: Language Science Press. DOI: (?P<doi>[^ ]*)")

def get_soup(book_ID):
    url = f"https://langsci-press.org/catalog/book/{book_ID}"
    html = requests.get(url).text
    if len(html) in (18920, 18922): #book not found
        return None
    print(f"{book_ID}", end=" ")
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def get_citeinfo(soup):
    try:
        citeinfo = soup.find("div", "series").findNext('div','label').nextSibling.nextSibling.text.strip()
    except AttributeError:
        print("could not retrieve citeinfo")
        return None
    if "orthcoming" in citeinfo:
        print("not published yet")
        return None
    citegroups = CITEPATTERN.match(citeinfo)
    if citegroups is None:
        print("could not match citeinfo")
    else:
        print()
    return citegroups

def get_blurb(soup):
    try:
        synopsis = soup.find("div", "main_entry").findNext('div','value').text.strip()
    except AttributeError:
        print("could not retrieve blurb")
        return None
    return synopsis

def get_publication_date(soup):
    try:
        #date = soup.find("div", "date_published").findNext('div','value').text.strip()
        date = soup.find("meta", {"name" : "citation_publication_date"}).attrs["content"]
        #months = {m:i+1 for i,m in enumerate("January February March April May June July August September October November December".split())}
        #print(date)
        #month, day, year = date.split()
        #numerical_month = months[month]
        #if int(numerical_month) < 10:
            #numerical_month = f"0{numerical_month}"
        #formatted_date =  "%s-%s-%s" % (year.strip(),numerical_month,day.replace(",",''))
        #return formatted_date
        return date
    except AttributeError:
        print("could not retrieve publication date")
        return None
    return date


def get_ISBNs(soup, drophyphens=True):
    dropee = ""
    if drophyphens:
        dropee = '-'
    isbns = {}
    publicationformats = soup.find_all("div", "publication_format")
    for publicationformat in publicationformats:
        item_heading = publicationformat.find("div", "item_heading")
        try:
            label = item_heading.find("div").text.strip()
        except AttributeError:
            continue
        if label == "Softcover":
            isbns['softcover'] = publicationformat.find("div", "identification_code").find('div').text.strip().replace(dropee, '')
            continue
        if label == "Hardcover":
            isbns['hardcover'] = publicationformat.find("div", "identification_code").find('div').text.strip().replace(dropee, '')
            continue
        if "PDF" in label:
            try:
                isbns['digital'] = publicationformat.find("div", "identification_code").find('div').text.strip().replace(dropee, '')
            except AttributeError:
                pass
    return isbns





def get_ISBN_digital(soup, drophyphens=True):
    return get_ISBNs(soup, drophyphens=True)['digital']

def get_ISBN_softcover(soup, drophyphens=True):
    return get_ISBNs(soup, drophyphens=True)['softcover']

def get_ISBN_hardcover(soup, drophyphens=True):
    return get_ISBNs(soup, drophyphens=True)['hardcover']


#def get_ISBN_softcover(soup, drophyphens=True):
    #ISBNlabel = soup.find("div", "identification_code").findNext('h3')
    #labeltext = ISBNlabel.text.strip()
    #if labeltext == "ISBN-13 (15)":
        #ISBNvalue = ISBNlabel.findNext("div","value")
        #if drophyphens:
            #return ISBNvalue.text.strip().replace("-","")
        #else:
            #return ISBNvalue.text.strip()


#def get_ISBN_hardcover(soup, drophyphens=True):
    #ISBNlabel = soup.find("div", "identification_code").findNext('h3')
    #labeltext = ISBNlabel.text.strip()
    #if labeltext == "ISBN-13 (15)":
        #ISBNvalue = ISBNlabel.findNext("div","value")
        #if drophyphens:
            #return ISBNvalue.text.strip().replace("-","")
        #else:
            #return ISBNvalue.text.strip()

def get_biosketches(soup):
    container = soup.find("div", "author_bios")
    creators = container.find_all("div", "sub_item")
    result = [(creator.find("div", "label").text.strip(),
               creator.find("div", "value").text.strip()
               ) for creator in creators]
    return result


def get_title_subtitle(citegroup):
    try:
        titlestring = citegroup["title"]
    except TypeError:
        return None, None
    title_elements = titlestring.split(": ")
    title = title_elements[0]
    try:
        subtitle = title_elements[1]
    except IndexError:
        subtitle = ""
    return title, subtitle

def biosketches2names(biosketches):
    resultlist = []
    for i, biosketch in enumerate(biosketches):
        name = biosketch[0]
        sketch = biosketch[1]
        nameparts = name.split(',')[0].split() #throw away affiliation
        firstname = ' ' .join(nameparts[0:-1])
        lastname = nameparts[-1]
        resultlist.append((firstname, lastname, sketch))
    return resultlist


def get_wiki_citation(creatorlist):
    vauthors = ''
    wikiauthors = ''
    if citeinfo['ed']:
        creatortype = 'veditors'
    else:
        creatortype = 'vauthors'
    wikicreators = ", ".join([u"%s %s"%(authormetadata[1],
                                        ''.join([firstname[0]
                                                    for firstname
                                                    in authormetadata[0].split()
                                                    ])
                                        )
                                for authormetadata
                                in creatorlist
                                ]
                    )
    wikiinfo = f"""<ref name="xxx">{{Cite book
    | {creatortype} = {wikicreators}
    | title =   %s%s
    | place = Berlin
    | publisher = Language Science Press
    | date = {publication_date}
    | format = pdf
    | url = http://langsci-press.org/catalog/book/{book_ID}
    | doi = {doi}
    | doi-access=free
    | isbn = {isbndigital}
    }}
    </ref>"""
    return wikiinfo


def get_pdf(soup, file_name):
    publication_formats = soup.find("div", "files")
    #print(publication_formats)
    try:
        zenodolink = [el['href'] for el in publication_formats.find_all("a") if el['href'].startswith('https://zenodo')][0]
        with open(file_name, "wb") as out:
            response = requests.get(zenodolink)
            out.write(response.content)
    except IndexError:
        omplinks_pdf = [el['href'] for el in publication_formats.find_all("a","pdf")]
        #print(omplinks_pdf)
        if len(omplinks_pdf) > 1:
           print('more than one pdf')
           return
        omplink_pdf = omplinks_pdf[0]
        with open(file_name, "wb") as out:
            response = requests.get(omplink_pdf)
            out.write(response.content)
        #treat omp link`








#out = codecs.open("wikiinfo.txt","w",encoding="utf-8")
#out.write("""<ref name="xxx">{{Cite book
#| %s
#| title =   %s%s
#| place = Berlin
#| publisher = Language Science Press
#| date = %s
#| format = pdf
#| url = http://langsci-press.org/catalog/book/%s
#| doi =
#| doi-access=free
#| isbn = %s
#}}
#</ref>

