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
        date = soup.find("div", "date_published").findNext('div','value').text.strip()
        months = {m:i+1 for i,m in enumerate("January February March April May June July August September October November December".split())}
        month, day, year = date.split()
        numerical_month = months[month]
        if int(numerical_month) < 10:
            numerical_month = f"0{numerical_month}"
        formatted_date =  "%s-%s-%s" % (year.strip(),numerical_month,day.replace(",",''))
        print(formatted_date)
        return formatted_date
    except AttributeError:
        print("could not retrieve publication date")
        return None
    return date


def get_ISBN_digital(soup, drophyphens=True):
    ISBNlabel = soup.find("div", "identification_code").findNext('h3')
    labeltext = ISBNlabel.text.strip()
    if labeltext == "ISBN-13 (15)":
        ISBNvalue = ISBNlabel.findNext("div","value")
        if drophyphens:
            return ISBNvalue.text.strip().replace("-","")
        else:
            return ISBNvalue.text.strip()

def get_biosketches(soup):
    container = soup.find("div", "author_bios")
    creators = container.find_all("div", "sub_item")
    result = [(creator.find("div", "label").text.strip(),
               creator.find("div", "value").text.strip()
               ) for creator in creators]
    return result






