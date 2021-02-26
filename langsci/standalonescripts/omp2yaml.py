import pprint
import yaml
from sqlalchemy import create_engine

# reviews
# select * from langsci_submission_links; #old style reviews


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

prefixselector ="""
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
        return ''

def get_proofreaders(book_id):
    proofreaders = [" ".join([y for y in x if y]) for x in conn.execute(proofreadersselector % book_id).fetchall()]
    return proofreaders

def get_doi(book_id):
    return get_one(doiselector, book_id)

def get_prefix(book_id):
    return get_one(prefixselector, book_id).replace(':', '')


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
    #print(creators)
    authors = [au[:4] for au in creators if au[4] == 'AU'] #AU is code for user role 'author'
    editors = [ed[:4] for ed in creators if ed[4] == 'VE'] #VE is code for user role 'editor'
    return {'authors': authors, 'editors': editors}

def get_isbns(book_id):
    digital = get_one(isbndigitalselector, book_id)
    hardcover = get_one(isbnhardcoverselector, book_id)
    softcover = get_one(isbnsoftcoverselector, book_id)
    return {"digital": digital, "softcover": softcover, "hardcover": hardcover}

def get_reviews(book_id):
    reviews = [list(x) for x in conn.execute(rezensionselector % book_id).fetchall()]
    return [{"reviewer": t[0],
             "money_quote": t[1],
             "date": t[2],
             "link": t[3],
             "link_name": t[4]
            } for t in reviews]

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
        chapter_authors = [list(x) for x in conn.execute(chapterauthorsselector % chapter_id).fetchall()]
        chapters.append({"number":running_number+1, "title": chapter_main_title,"subtitle": chapter_subtitle, "authors": chapter_authors}) # chapter number, subtitle, chapterdoi
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
        "blurb": get_one(abstractselector, t[0]).replace('<p>','').replace('</p>',''),
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

#check repeating contributors; author/editor; tbls/other
xmlbooktemplate =f"""<Product>
    <RecordReference>langsci-press.org/{book_id}</RecordReference>
    <NotificationType>03</NotificationType>
    <RecordSourceType>01</RecordSourceType>
    <RecordSourceIdentifierType>05</RecordSourceIdentifierType>
    <RecordSourceIdentifier>978-3-98554</RecordSourceIdentifier>
    <RecordSourceName>Language Science Press</RecordSourceName>
    <ProductIdentifier>
        <ProductIDType>06</ProductIDType>
        <IDValue>{doi}</IDValue>
    </ProductIdentifier>
    <ProductIdentifier>
        <ProductIDType>15</ProductIDType>
        <IDValue>{isbn}</IDValue>
    </ProductIdentifier>
    <ProductForm>DG</ProductForm>
    <EpubType>002</EpubType>
    <SeriesIdentifier>
        <SeriesIDType>02</SeriesIDType>
        <IDValue>{issn}</IDValue>
    </SeriesIdentifier>
    <TitleOfSeries>{seriesname}</TitleOfSeries>
    <Title>
        <TitleType>01</TitleType>
        <TitleText textcase="01">{bookmaintitle}</TitleText>
        <Subtitle> textcase="01">{booksubtitle}</Subtitle>
    </Title>
    <Contributor>
        <SequenceNumber>{contributorsequencenumber}</SequenceNumber>
        <ContributorRole>A01 author /B01 editor </ContributorRole>
        <NamesBeforeKey>{first_name} {middle_name}</NamesBeforeKey>
        <KeyNames>{last_name}</KeyNames>
        <ProfessionalAffiliation>
            <Affiliation>{affiliation}</Affiliation>
        </ProfessionalAffiliation>
        <BiographicalNote>{biosketch}</BiographicalNote>
    </Contributor>
    <NumberWithinSeries>{seriesnumber}</NumberWithinSeries>
    <EditionNumber>{edition}</EditionNumber>
    <Language>
        <LanguageRole>01</LanguageRole>
        <LanguageCode>{language}</LanguageCode>
    </Language>
    <NumberOfPages>{numberofpages}</NumberOfPages>
    <BASICMainSubject>LAN009000</BASICMainSubject>
    <AudienceCode>06 (general) 05 (tbls)</AudienceCode>
    <OtherText>
        <TextTypeCode>01</TextTypeCode>
        <Text>{blurb}</Text>
    </OtherText>
    <OtherText>
        <TextTypeCode>05</TextTypeCode>
        <Text>{reviewquote}</Text>
    </OtherText>
    <MediaFile>
        <MediaFileTypeCode>04</MediaFileTypeCode>
         <MediaFileFormatCode>09</MediaFileFormatCode>
         <MediaFileLinkTypeCode>01<MediaFileLinkTypeCode>
         <MediaFileLink>{coverurl}</MediaFileLink>
    </MediaFile>
    <ProductWebsite>
        <WebsiteRole>02<WebsiteRole>
        <ProductWebsiteLink>{bookurl}</ProductWebsiteLink>
    </ProductWebsite>

    <Imprint>
        <ImprintName>Language Science Press</ImprintName>
    </Imprint>
    <Publisher>
        <PublishingRole>01</PublishingRole>
        <PublisherName>Language Science Press</PublisherName>
        <NameCodeType>05</NameCodeType>
        <NameCodeType>978-3-98554</NameCodeType>
        <Website>
                <WebsiteRole>01</WebsiteRole>
                <WebsiteLink>https://www.langsci-press.org</WebsiteLink>
        </Website>
    </Publisher>
    <CityOfPublication>Berlin</CityOfPublication>
    <CountryOfPublication>DE</CountryOfPublication>
    <PublishingStatus>04</PublishingStatus>
    <PublicationDate>{year}</PublicationDate>
    <Measure>
        <MeasureTypeCode>01</MeasureTypeCode>
        <Measurement>24.00</Measurement>
        <MeasureUnitCode>cm</MeasureUnitCode>
    </Measure>
    <Measure>
        <MeasureTypeCode>02</MeasureTypeCode>
        <Measurement>17.00</Measurement>
        <MeasureUnitCode>cm</MeasureUnitCode>
    </Measure>
</Product>
"""

def to_yaml():
    for book in books:
        with open("tmp/%s.yaml"%book, 'w') as yamlout:
            yamlout.write(yaml.dump(books[book]))
        with open("tmp/%s.md"%book, 'w') as mdout:
            mdout.write(mdbooktemplate%(books[book]["series"],book,book))
        for chapter in books[book]['chapters']:
            chapternumber = chapter['number']
            with open("tmp/%s-%s.md"%(book,chapternumber), 'w') as chapterout:
                chapterout.write(mdchaptertemplate%(book,chapternumber,book,chapternumber,book,chapternumber))


def to_onix():
    for book in books:
        with open("onix-xml/%s.xml"%book, 'w') as xmlout:
            xmlout.write("")
        for chapter in books[book]['chapters']:
            chapternumber = chapter['number']
            with open("onix-xml/%s-%s.xml"%(book,chapternumber), 'w') as chapterout:
                chapterout.write("")

if __name__ == "__main__":
    to_onix()

















