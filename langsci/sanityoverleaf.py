from sanitycheck import LSPDir
import re
import git 
import os
import sys
import subprocess


def cloneorpull(url):
    m = re.search('([0-9]{7,}[a-z]+)',overleafurl)
    overleafID = m.group(1)
    print "overleaf ID found:", overleafID
    giturl = "https://git.overleaf.com/"+overleafID
    gitdir = os.path.join(os.getcwd(),overleafID)
    print "git repo is ", giturl
    try:
        git.Repo.clone_from(giturl, gitdir)
        print "cloned"
    except git.exc.GitCommandError:
        print "repo already in file system. Pulling"        
        cwd = os.getcwd()
        print gitdir
        os.chdir(gitdir)
        subprocess.call(["git","pull"]) 
        os.chdir(cwd)
        print "pulled"
    return gitdir
        
    return lspdir
    
    
if __name__ == "__main__":
    overleafurl = sys.argv[1]
    d = cloneorpull(overleafurl)
    lspdir = LSPDir(os.path.join(d,'chapters'))
    print "checking %s" % ' '.join([f for f in lspdir.texfiles+lspdir.bibfiles])
    lspdir.check()
    lspdir.printErrors()