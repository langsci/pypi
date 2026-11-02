from newick import read
import re
GLOTTOCODE = re.compile("'(.*) \[([a-z0-9]{4}[0-9]{4})\]")
families = read('tree_glottolog_newick.txt')

d = {}

def process(node, ancestors):
    try:
        name, glottocode = GLOTTOCODE.search(node._name).groups()
    except AttributeError:
        print("no glottocode", node)
    # print(glottocode, ancestors)
    d[glottocode] = ancestors
    for descendant in node.descendants:
        process(descendant, ancestors+[(glottocode, name)])

for family in families:
    process(family, [])



