import requests
from bs4 import BeautifulSoup

def string2glottocode(language_name):
    request_url = (
        f"https://glottolog.org/glottolog?name={language_name}&namequerytype=part"
    )
    html = requests.get(request_url).text
    soup = BeautifulSoup(html, "html.parser")
    languoids = soup.find_all("a", class_="Language")
    #glottocode = None
    #print(len(languoids))
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
        request_url = f"https://glottolog.org/resource/languoid/id/{glottocode}"
        html = requests.get(request_url).text
        soup = BeautifulSoup(html, "html.parser")
        try:
            iso = soup.find("span", class_="iso639-3").a["title"]
        except AttributeError:
            return "und"
        return iso

