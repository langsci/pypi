import requests
from bs4 import BeautifulSoup
import re

def string2glottocode(language_name):
    request_url = f"https://glottolog.org/glottolog?search={language_name}"
    html = requests.get(request_url).text
    soup = BeautifulSoup(html, "html.parser")
    try:
        # extract glottocode from rdf link (only place in literal HTML)
        glottocode = soup.find_all("link", {"rel": "alternate"})[0]["href"][-12:-4]
    except IndexError:
        languoids = soup.find_all("a", class_="Language")
        # glottocode = None
        if len(languoids) == 0:  # no languoids. We store this in persistent storage
            glottocode = None
        elif len(languoids) == 3:  # exactly one languoid (there are three a's per langu
            glottocode = languoids[0]["title"]
            # language_family = languoids[2]["title"]
        else:  # more than one languoid.  We check whether Glottolog has exactly one "language"
            languoids2 = soup.find_all("td", class_="level-language")
            if len(languoids2) == 1:
                glottocode = (
                    languoids2[0].find("a", class_="Language")["href"].split("/")[-1]
                )
                # language_family = #FIXME
            else:  # Glottolog has no clear indication of the language. We keep this information in temporary storage
                glottocode = False
    return glottocode


def glottocode2iso(glottocode):
    # print("using glottocode2iso for", glottocode)
    request_url = f"https://glottolog.org/resource/languoid/id/{glottocode}"
    html = requests.get(request_url).text
    soup = BeautifulSoup(html, "html.parser")
    try:
        iso = soup.find("span", class_="iso639-3").a["title"]
    except AttributeError:
        return "und"
    return iso


def glottocode2name(glottocode):
    print("using glottocode2name for", glottocode)
    request_url = f"https://glottolog.org/resource/languoid/id/{glottocode}"
    html = requests.get(request_url).text
    soup = BeautifulSoup(html, "html.parser")
    try:
        name = soup.find("h3").find("span").text
    except AttributeError:
        print(f"name for {glottocode} could not be established")
        return ""
    print(glottocode, name)
    return name



def glottocode2countries(glottocode):
    print("using glottocode2countries for", glottocode)
    request_url = f"https://glottolog.org/resource/languoid/id/{glottocode}"
    html = requests.get(request_url).text
    soup = BeautifulSoup(html, "html.parser")
    try:
        links = soup.find("div",{"id":"acc-countries"}).find_all('a')
        countrycodes = [{"ISO3166":a["href"].split("=")[-1], "label": a.text.strip().split(' [')[0]} for a in links]
    except AttributeError:
        print(f"countries for {glottocode} could not be established")
        countrycodes = []
    print(glottocode, countrycodes)
    return countrycodes



def glottocode2geocoords(glottocode):
    print("using glottocode2geocoords for", glottocode)
    request_url = f"https://glottolog.org/resource/languoid/id/{glottocode}"
    html = requests.get(request_url).text
    soup = BeautifulSoup(html, "html.parser")
    try:
        mapdiv = soup.find("div",{"id":"map-container"})
        script = mapdiv.find('script').text
        longitude, latitude = re.search('"longitude": ([-0-9.]+), "latitude": ([-0-9.]+)', script).groups()
        coords = (float(longitude), float(latitude))
    except AttributeError:
        print(f"coords for {glottocode} could not be established")
        coords = []
    # print(glottocode, coords)
    return coords
