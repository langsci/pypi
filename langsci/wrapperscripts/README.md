# Wrapper scripts
This directory contains scripts which make use of the `langsci` library to accomplish various tasks. The scripts are:

- `autoindex.py`: read all terms in the files `localsubjectterms.txt` and `locallanguages.txt` and add LaTeX indexing commands around all occurrences of these terms for all `*tex` files contained in the folder `chapters/`

- `bodxml2.py`: retrieve metadata for a given LangSci ID and prepare an XML file for upload to the BoD print on demand service. Also package the relevant pdf files together with the metadata in a zip archive according to BoD specifications.


- `cldf2imtvault.py`: read a CSV file of all examples from LangSci/Glossa and output them in JSON for ingestion into IMTVault

<!-- - `deduplicate_bib.py` -->

- `doc2tex.py`: take an `odt` file and convert it into `tex`

- `fixindex.py`: make sure that indexed terms with díâçŕïţıčš are sorted properly in LaTeX indexes

- `generate_catalog.py`: retrieve metadata from the website and write it to a csv file

- `generate_ebsco.py`: retrieve metadata from the website and write it to an xlsx file for EBSCO

- `generate_proquest.py`: retrieve metadata from the website and write it to xml files for ProQuest

- `generate_scopus.py`: retrieve metadata from the website and write it to ONIX xml files for Scopus

- `normalizebib.py`: conform a bib file to LangSci guidelines. Take care of field names and protect some terms and letters from decapitalization. Mark violations of the guidelines with `\biberror{}`

- `registerzenodo.py`: register a book with Zenodo. Mostly useful for edited volumes. Chapters are registered as well and the retrieved DOI is inserted into the chapter files

- `sanitygit.py`: check the LangSci GitHub repository for a given ID for compliance with the guidelines

- `sanitylocal.py`: check a local project compliance with the guidelines


- `titlemapping.py`: metadata for LangSci titles

- `txt2bib.py`: convert a plain text file with bib records (one per line) into `BibTeX`

- `wikicite.py`: retrieve metadata from the website and output it according to wikipedia reference syntax







