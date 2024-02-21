import glob
from validation import validation_tuples
import re
import random
from collections import defaultdict

book_ids = glob.glob("store/*")
threshold = 200
excount = 0

d = defaultdict(dict)

print(book_ids)
while excount < threshold:
    book_id = random.choice(book_ids)
    # print(book_id)
    files = glob.glob(f"{book_id}/*tex")
    # print(files)
    filename = random.choice(files)
    # print(filename)
    with open(filename) as infile:
        try:
            content = infile.read()
        except UnicodeDecodeError:
            pass
        candidates = re.split(r"(\\glll?)(?!l)", content)
        try:
            glls = candidates[1:]
            keywords = glls[::2]
            imts = glls[1:][::2]
            examples = list(zip(keywords, imts))
            example = random.choice(examples)
            keyword = example[0]  # gll or glll
            imt = (
                example[1]
                .split(r"\z")[0]
                .split(r"\end{exe}")[0]
                .split(r"\end{xlist}")[0]
                .split(r"\ex")[0]
                .split("\n")[:10]
            )
            condensed_imt = "\n".join(imt)
            if (keyword, condensed_imt) not in d:
                d[filename][(keyword, condensed_imt)] = True
                excount += 1
        except IndexError:
            pass

with open("validationexamples.txt", "w") as out:
    for fn in sorted(d.keys()):
        for ex in d[fn]:
            out.write(40 * "=")
            out.write("\n")
            out.write(fn)
            out.write("\n")
            out.write(ex[0])
            out.write(ex[1])
            out.write("\n")
