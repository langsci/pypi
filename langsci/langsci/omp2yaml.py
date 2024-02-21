import pprint
import yaml
from sqlalchemy import create_engine
from langdetect import detect_langs, lang_detect_exception
from xml.sax.saxutils import escape
from datetime import datetime
from lxml import etree
from io import StringIO

# reviews
# select * from langsci_submission_links; #old style reviews


schemafilename = "ONIX_BookProduct_3.0_reference.xsd"
schemacontent = open(schemafilename).read()
schemaXML = etree.parse(StringIO(schemacontent))

subtitleselector = """select setting_value
from submission_settings
where setting_name = 'subtitle'
and submission_id = %s
;
"""

abstractselector = """select setting_value
from submission_settings
where setting_name = 'abstract'
and submission_id = %s
;
"""

remote_urlselector = """select remote_url
from  publication_formats
where remote_url is not NULL
and remote_url != ''
and publication_formats.submission_id=%s
order by remote_url;
"""

doiselector = """select setting_value
from submissions, publication_formats, publication_format_settings
where setting_name="pub-id::doi"
and publication_formats.submission_id = submissions.submission_id
and publication_formats.publication_format_id=publication_format_settings.publication_format_id
and submissions.submission_id=%s
;
"""
isbndigitalselector = """
select value from  publication_formats, identification_codes
where code=15
and identification_codes.publication_format_id = publication_formats.publication_format_id
and publication_formats.submission_id=%s
;
"""
isbnhardcoverselector = """
select value from  publication_formats, identification_codes
where code=28
and identification_codes.publication_format_id = publication_formats.publication_format_id
and publication_formats.submission_id=%s
;
"""

isbnsoftcoverselector = """
select value from  publication_formats, identification_codes
where code=29
and identification_codes.publication_format_id = publication_formats.publication_format_id
and publication_formats.submission_id=%s
;
"""

creatorselector = """
select first_name, middle_name, last_name, author_settings.setting_value as biosketch, user_group_settings.setting_value as authoreditor
from authors, user_group_settings, author_settings
where include_in_browse = 1
and authors.submission_id = %s
and authors.user_group_id = user_group_settings.user_group_id
and author_settings.author_id=authors.author_id
and author_settings.setting_name='biography'
;
"""

chaptersselector = """
 select submission_chapters.chapter_id, submission_chapter_settings.setting_value as title
 from submission_chapters, submission_chapter_settings
 where submission_chapters.chapter_id=submission_chapter_settings.chapter_id
 and submission_chapter_settings.setting_name="title"
 and submission_chapters.submission_id=%s
;
"""

chapterauthorsselector = """
 select first_name, middle_name, last_name
 from authors, submission_chapters, submission_chapter_authors
 where submission_chapters.chapter_id=submission_chapter_authors.chapter_id
 and authors.author_id = submission_chapter_authors.author_id
 and submission_chapters.chapter_id=%s
 ;
"""

prefixselector = """
select setting_value from submission_settings
where setting_name='prefix'
and submission_id = %s
;
"""

proofreadersselector = """
select first_name, middle_name, last_name
from users, stage_assignments
where stage_assignments.user_group_id = 7
and users.user_id = stage_assignments.user_id
and stage_assignments.submission_id=%s
"""


rezensionselector = """
select reviewer, money_quote, date, link, link_name
from langsci_review_links
where submission_id =%s
"""


def get_one(selector, book_id):
    tuple_ = conn.execute(selector % book_id).fetchone()
    try:
        return tuple_[0]
    except TypeError:
        return ""


def get_proofreaders(book_id):
    proofreaders = [
        " ".join([y for y in x if y])
        for x in conn.execute(proofreadersselector % book_id).fetchall()
    ]
    return proofreaders


def get_doi(book_id):
    return get_one(doiselector, book_id)


def get_prefix(book_id):
    return get_one(prefixselector, book_id).replace(":", "")


def get_urls(book_id):
    urls = conn.execute(remote_urlselector % book_id).fetchall()
    d = {}
    amazonfound = False
    for t in urls:
        url = t[0]
        if "paperhive" in url:
            d["paperhive"] = url
            continue
        if "amazon" in url and not amazonfound:
            amazonfound = True
            amazon_id = url.split("?")[0].split("/")[-1]
            d["amazon.com"] = (
                "https://www.amazon.com/dp/%s?tag=wwwlangscipre-20" % amazon_id
            )
            d["amazon.co.uk"] = (
                "https://www.amazon.co.uk/dp/%s?tag=wwwlangscip03-21" % amazon_id
            )
            d["amazon.co.de"] = (
                "https://www.amazon.de/dp/%s?tag=wwwlangscipre-21" % amazon_id
            )
    return d


def get_book_creators(book_id):
    creators = [list(x) for x in conn.execute(creatorselector % book_id).fetchall()]
    # print(creators)
    authors = [
        au[:4] for au in creators if au[4] == "AU"
    ]  # AU is code for user role 'author'
    editors = [
        ed[:4] for ed in creators if ed[4] == "VE"
    ]  # VE is code for user role 'editor'
    return {"authors": authors, "editors": editors}


def get_isbns(book_id):
    digital = get_one(isbndigitalselector, book_id)
    hardcover = get_one(isbnhardcoverselector, book_id)
    softcover = get_one(isbnsoftcoverselector, book_id)
    return {"digital": digital, "softcover": softcover, "hardcover": hardcover}


def get_reviews(book_id):
    reviews = [list(x) for x in conn.execute(rezensionselector % book_id).fetchall()]
    return [
        {
            "reviewer_name": t[0],
            "money_quote": t[1]
            .replace("<em", "<span>")
            .replace("</em>", "</span>")
            .replace("<it>", '<span style="font-style:italic;">')
            .replace("</it>", "</span>")
            .replace("allowfullscreen>", 'allowfullscreen="true">'),
            "date": t[2],
            "link": t[3],
            "link_name": t[4],
        }
        for t in reviews
    ]


def get_chapters(book_id):
    chapter_tuples = conn.execute(chaptersselector % book_id).fetchall()
    chapters = []
    for running_number, chapter in enumerate(chapter_tuples):
        chapter_id = chapter[0]
        whole_chapter_title = chapter[1]
        try:
            chapter_main_title, chapter_subtitle = whole_chapter_title.split(": ")
        except ValueError:
            chapter_main_title = whole_chapter_title
            chapter_subtitle = None
        chapter_authors = [
            list(x)
            for x in conn.execute(chapterauthorsselector % chapter_id).fetchall()
        ]
        chapters.append(
            {
                "number": running_number + 1,
                "title": chapter_main_title,
                "subtitle": chapter_subtitle,
                "authors": chapter_authors,
            }
        )  # chapter number, subtitle, chapterdoi
    return chapters


initial_query = """
select distinct submissions.submission_id, path, series_position, submission_settings.setting_value as title, date
from submissions, series, series_settings, submission_settings, publication_formats, publication_dates, publication_format_settings, published_submissions
 where
 submissions.series_id=series.series_id
 and series_settings.setting_name = 'title'
 and series_settings.locale="en_US"
 and submissions.series_id=series_settings.series_id
 and submission_settings.submission_id = submissions.submission_id
 and submission_settings.setting_name = 'title'
 and publication_formats.submission_id = submissions.submission_id
 and publication_format_settings.setting_value="PDF"
 and publication_formats.publication_format_id = publication_format_settings.publication_format_id
 and publication_dates.publication_format_id=publication_formats.publication_format_id
 and published_submissions.submission_id=submissions.submission_id
 and published_submissions.submission_id is not NULL
 ;
"""
engine = create_engine("mysql://snordhoff:123@localhost/omp")
conn = engine.connect()
rawbooks = conn.execute(initial_query).fetchall()
books = {
    t[0]: {
        "bookid": t[0],
        "prefix": get_prefix(t[0]),
        "title": t[3],
        "series": t[1],
        "seriesnumber": t[2],
        "booksubtitle": get_one(subtitleselector, t[0]),
        "blurb": get_one(abstractselector, t[0])
        .replace("<em", "<span")
        .replace("</em>", "</span>")
        .replace("<it>", '<span style="font-style:italic">')
        .replace("</it>", "</span>")
        .replace("<blockquote>", "<blockquote><p>")
        .replace("</blockquote>", "</p></blockquote>")
        .replace("<hr>", "<hr />")
        .replace("<br>", "<br />")
        .replace('align="justify"', ""),
        "doi": get_doi(t[0]),
        "isbns": get_isbns(t[0]),
        "remote_urls": get_urls(t[0]),
        "creators": get_book_creators(t[0]),
        "chapters": get_chapters(t[0]),
        "proofreaders": [],
        "typesetters": [],
        "illustrators": [],
        "publicationdate": t[4],
        "proofreaders": get_proofreaders(t[0]),
        "reviews": get_reviews(t[0]),
    }
    for t in rawbooks
}

mdbooktemplate = """---
layout: book
bookseries: %s
bookid: %s
permalink: book/%s
---"""

mdchaptertemplate = """---
layout: chapter
bookid: %s
chapternumber: %s
title: %s-%s
permalink: /chapters/%s-%s
---"""

# <ONIXMessage release="3.0" xmlns="http://ns.editeur.org/onix/3.0/reference">

# xmlheader = """<?xml version="1.0" encoding="UTF-8"?>
xmlheader = """<?xml version="1.0"?>
<ONIXMessage xmlns="http://ns.editeur.org/onix/3.0/reference" release="3.0">
<Header>
    <Sender>
        <SenderIdentifier>
            <SenderIDType>05</SenderIDType>
            <IDValue>978-3-98554</IDValue>
        </SenderIdentifier>
        <SenderName>Language Science Press</SenderName>
        <ContactName>Sebastian Nordhoff</ContactName>
        <EmailAddress>support@langsci-press.org</EmailAddress>
    </Sender>
    <Addressee>
        <AddresseeName>Scopus</AddresseeName>
    </Addressee>
    <SentDateTime>{}</SentDateTime>
</Header>
""".format(
    datetime.today().strftime("%Y%m%d")
)

xmlfooter = """</ONIXMessage>"""


def to_yaml():
    for book in books:
        with open("tmp/%s.yaml" % book, "w") as yamlout:
            yamlout.write(yaml.dump(books[book]))
        with open("tmp/%s.md" % book, "w") as mdout:
            mdout.write(mdbooktemplate % (books[book]["series"], book, book))
        for chapter in books[book]["chapters"]:
            chapternumber = chapter["number"]
            with open("tmp/%s-%s.md" % (book, chapternumber), "w") as chapterout:
                chapterout.write(
                    mdchaptertemplate
                    % (book, chapternumber, book, chapternumber, book, chapternumber)
                )


def to_onix():
    xmlbooktemplate = """<Product>
    <RecordReference>langsci-press.org/{bookid}</RecordReference>
    <NotificationType>03</NotificationType>
    <RecordSourceType>01</RecordSourceType>
    <RecordSourceIdentifier>
        <RecordSourceIDType>05</RecordSourceIDType>
        <IDValue>978-3-98554</IDValue>
    </RecordSourceIdentifier>
    <RecordSourceName>Language Science Press</RecordSourceName>
    <ProductIdentifier>
        <ProductIDType>06</ProductIDType>
        <IDValue>{doi}</IDValue>
    </ProductIdentifier>
    <ProductIdentifier>
        <ProductIDType>15</ProductIDType>
        <IDValue>{isbndigital}</IDValue>
    </ProductIdentifier>
    <DescriptiveDetail>
<!-- P.3 -->
    <ProductComposition>00</ProductComposition>
        <ProductForm>ED</ProductForm>
        <!-- <EpubType>002</EpubType> -->
        <Measure>
            <MeasureType>01</MeasureType>
            <Measurement>24.00</Measurement>
            <MeasureUnitCode>cm</MeasureUnitCode>
        </Measure>
        <Measure>
            <MeasureType>02</MeasureType>
            <Measurement>17.00</Measurement>
            <MeasureUnitCode>cm</MeasureUnitCode>
        </Measure>
        <Collection>
            <CollectionType>10</CollectionType>
            <CollectionIdentifier>
                <CollectionIDType>02</CollectionIDType>
                <IDValue>{issn}</IDValue>
            </CollectionIdentifier>
            {collectionsequence}
        </Collection>
        <TitleDetail>
            <TitleType>01</TitleType>
            <TitleElement>
                <TitleElementLevel>01</TitleElementLevel>
                <TitleText textcase="01">{title}</TitleText>{subtitlestring}
            </TitleElement>
            <TitleElement>
                <TitleElementLevel>02</TitleElementLevel>
                <TitleText textcase="02">{seriesname}</TitleText>
            </TitleElement>
        </TitleDetail>
        {contributorstring}
        <EditionNumber>{edition}</EditionNumber>
        <Language>
            <LanguageRole>01</LanguageRole>
            <LanguageCode>{language}</LanguageCode>
        </Language>
        <Subject>
            <MainSubject/>
            <SubjectSchemeIdentifier>10</SubjectSchemeIdentifier>
            <SubjectSchemeVersion>2009</SubjectSchemeVersion>
            <SubjectCode>LAN009000</SubjectCode>
        </Subject>
        <AudienceCode>{audiencecode}</AudienceCode>
    </DescriptiveDetail>
    <CollateralDetail>
        <TextContent>
            <TextType>03</TextType>
            <ContentAudience>00</ContentAudience>
            <Text textformat="05">
                {blurb}
            </Text>
        </TextContent>
        {reviewstring}
        <SupportingResource>
            <ResourceContentType>01</ResourceContentType>	<ContentAudience>00</ContentAudience>
            <ResourceMode>03</ResourceMode>
            <ResourceVersion>
                <ResourceForm>02</ResourceForm>
                <ResourceVersionFeature>
                <ResourceVersionFeatureType>01</ResourceVersionFeatureType>
                <FeatureValue>D503</FeatureValue>
                </ResourceVersionFeature>
                <ResourceLink>{coverurl}</ResourceLink>
            </ResourceVersion>
        </SupportingResource>
    </CollateralDetail>
    <PublishingDetail>
        <Publisher>
            <PublishingRole>01</PublishingRole>
            <PublisherName>Language Science Press</PublisherName>
            <Website>
                    <WebsiteRole>01</WebsiteRole>
                    <WebsiteLink>https://www.langsci-press.org</WebsiteLink>
            </Website>
        </Publisher>
        <CityOfPublication>Berlin</CityOfPublication>
        <CountryOfPublication>DE</CountryOfPublication>
        <PublishingStatus>04</PublishingStatus>
        <PublishingDate>
            <PublishingDateRole>01</PublishingDateRole>
            <Date dateformat="00">{publicationdate}</Date>
        </PublishingDate>
    </PublishingDetail>
</Product>
"""

    seriesd = {
        "algad": ["African Language Grammars and Dictionaries", "2512-4862"],
        "cal": ["Contemporary African Linguistics", "2511-7726"],
        "cam": ["Contact and Multilingualism", "2700-855X"],
        "cfls": ["Conceptual Foundations of Language Science", "2363-877X"],
        "classics": ["Classics in Linguistics", "2366-374X"],
        "cmle": ["Computational Models of Language Evolution", "2364-7809"],
        "eotms": [
            "Empirically Oriented Theoretical Morphology and Syntax",
            "2366-3529",
        ],
        "eurosla": ["Eurosla Studies", "2626-2665"],
        "hpls": ["History and Philosophy of the Language Sciences", "2629-172X"],
        "loc": ["Languages of the Caucasus", "2699-0156"],
        "lv": ["Language Variation", "2366-7818"],
        "mi": ["Morphological Investigations", "2567-742X"],
        "nccs": ["Niger-Congo Comparative Studies", "2627-0048"],
        "mcnc": ["Niger-Congo Comparative Studies", "2627-0048"],
        "ogs": ["Open Generative Syntax", "2568-7336"],
        "osl": ["Open Slavic Linguistics", "2627-8332"],
        "pmwe": ["Phraseology and Multiword Expressions", "2625-3127"],
        "scl": ["Studies in Caribbean Languages", "2627-1834"],
        "sidl": ["Studies in Diversity Linguistics", "2363-5568"],
        "silp": ["Studies in Laboratory Phonology", "2363-5576"],
        "tbls": ["Textbooks in Language Sciences", "2364-6209"],
        "tgdi": ["Topics at the Grammar-Discourse Interface", "2567-3335"],
        "tmnlp": [
            "Translation and Multilingual Natural Language Processing",
            "2364-8899",
        ],
    }

    authortemplate = """<Contributor>
            <SequenceNumber>{}</SequenceNumber>
            <ContributorRole>A01</ContributorRole>
            <NamesBeforeKey>{} {}</NamesBeforeKey>
            <KeyNames>{}</KeyNames>
            <BiographicalNote>{}</BiographicalNote>
        </Contributor>"""

    editortemplate = """<Contributor>
            <SequenceNumber>{}</SequenceNumber>
            <ContributorRole>B01</ContributorRole>
            <NamesBeforeKey>{} {}</NamesBeforeKey>
            <KeyNames>{}</KeyNames>
            <BiographicalNote>{}</BiographicalNote>
        </Contributor>"""

    reviewtemplate = """
        <TextContent>
            <TextType>06</TextType>
            <ContentAudience>00</ContentAudience>
            <Text>{}</Text>
            <SourceTitle>{}​</SourceTitle>
        </TextContent>"""

    for book in books:
        if book in (16, 17, 18, 19, 22, 25):
            continue
        # if book not in (159, 192, 46,214,143,186,48,121,52,157,149,51,196,107,191,234,132,120,248,153,210,78,53):
        # continue
        # if book not in (200,):
        # continue
        with open("onix-xml/%s.xml" % book, "w") as xmlout:
            d = books[book]
            # pprint.pprint(d)
            d["subtitlestring"] = ""
            subtitle = d.get("booksubtitle", False)
            if subtitle:
                d["subtitlestring"] = f"\n            <Subtitle>{subtitle}</Subtitle>"
            d["isbndigital"] = books[book]["isbns"]["digital"]
            d["seriesname"] = seriesd[d["series"]][0]
            d["audiencecode"] = "06"  # academic
            if d["series"] == "tbls":
                d["audiencecode"] = "05"  # higher education
            d["issn"] = seriesd[d["series"]][1]
            d["contributorstring"] = ""
            offset = 1
            d["contributorstring"] += "\n        ".join(
                [
                    authortemplate.format(
                        i + offset, au[0], au[1], au[2], escape(au[3])
                    )
                    for i, au in enumerate(d["creators"]["authors"])
                ]
            )
            offset += len(d["creators"]["authors"])
            d["contributorstring"] += "\n        ".join(
                [
                    editortemplate.format(
                        i + offset, au[0], au[1], au[2], escape(au[3])
                    )
                    for i, au in enumerate(d["creators"]["editors"])
                ]
            )
            d["edition"] = 1
            try:
                toplanguage = detect_langs(" ".join([d["title"], d["booksubtitle"]]))[
                    0
                ].lang
            except:
                pprint.pprint(d)
            if toplanguage not in ["en", "fr", "de", "pt", "es", "zh"]:
                print("Unexpected language %s for %s." % (toplanguage, book))
            lgcode23 = {"de": "ger", "fr": "fre", "es": "esp", "ro": "por", "zh": "cmn"}
            toplanguage = lgcode23.get(toplanguage, "eng")
            # d['blurb'] = escape(d['blurb'])
            d["language"] = toplanguage
            d["reviewstring"] = ""
            d["reviewstring"] += "        ".join(
                reviewtemplate.format(review["money_quote"], review["reviewer_name"])
                for review in d["reviews"]
            )
            d["coverurl"] = (
                "https://langsci-press.org/$$$call$$$/submission/cover/cover?submissionId=%s"
                % d["bookid"]
            )
            d["bookurl"] = "https://langsci-press.org/catalog/book/%s" % d["bookid"]
            d["collectionsequence"] = ""
            try:
                d["seriesnumber"] = int(d["seriesnumber"])
                d[
                    "collectionsequence"
                ] = f"""<CollectionSequence>
                <CollectionSequenceType>02</CollectionSequenceType>
                <CollectionSequenceNumber>{d['seriesnumber']}</CollectionSequenceNumber>
            </CollectionSequence>
            """
            except ValueError:
                print(f"series number missing for {d['bookid']}")

            myxmlstring = (
                xmlheader
                + xmlbooktemplate.format(**d).replace("&nbsp;", " ")
                + xmlfooter
            )
            # xmldoc = etree.fromstring(myxmlstring)
            # schemaXML.validate(xmldoc)
            # schemafilename = "ONIX_BookProduct_3.0_reference.xsd"
            # etree.XMLSchema(etree.parse(open(schemafilename).read()))

            xmlout.write(myxmlstring)
        # for chapter in books[book]['chapters']:
        # chapternumber = chapter['number']
        # with open("onix-xml/%s-%s.xml"%(book,chapternumber), 'w') as chapterout:
        # chapterout.write("")


if __name__ == "__main__":
    to_onix()
    print("Completed. Run onixcheck -p onix-xml/")
