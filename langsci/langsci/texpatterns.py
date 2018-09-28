import re

INCLUDEPAPERP = re.compile(r"\n[\t ]*\\includepaper\{chapters/(.*?)\}")#only papers on new lines, ignoring % comments
BOOKAUTHORP = re.compile(r"\\author{(.*?)}")
LASTAND = re.compile(r"(\\lastand|\\and)")
CHAPTERAUTHORP = re.compile(r"\\author{(.*?) *\\affiliation{(.*)}")
TITLEP = re.compile(r"\\title{(.*?)}")
ISBNP = re.compile(r"\\lsISBNdigital}{(.*)}") 
CHAPTERKEYWORDSP = re.compile(r"\\keywords{(.*?)}")
ABSTRACTP = re.compile(r"\\abstract{(.*?)[}\n]")
BACKBODYP = re.compile(r"\\BackBody{(.*?)[}\n]")
KEYWORDSEPARATOR = re.compile("[,;-]")
PAGERANGEP = re.compile("{([0-9ivx]+--[0-9ivx]+)}")
BIBAUTHORP = re.compile(r"author={([^}]+)") #current setup adds space after author
BIBTITLEP = re.compile(r"title={{([^}]+)}}")