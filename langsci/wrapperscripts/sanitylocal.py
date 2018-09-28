import sys
try:
    import sanity
except ImportError:
    import langsci.sanity

try:
    directory = sys.argv[1]
except IndexError:
    pass
ignorecodes = []
try:
    ignorecodes  = sys.argv[2:]
except IndexError:
    pass
sanitydir = sanity.SanityDir(directory,ignorecodes)
print("checking %s with %i files" % (directory,len(sanitydir.texfiles+sanitydir.bibfiles+sanitydir.pngfiles+sanitydir.jpgfiles)))
sanitydir.check()
sanitydir.printErrors()
