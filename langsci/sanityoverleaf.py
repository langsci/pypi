from sanitycheck import LSPDir
import re
import  git 
import os
import sys
import subprocess

    
if __name__ == "__main__":
    overleafurl = sys.argv[1]
    m = re.search('([0-9]{7,}[a-z]+)',overleafurl)
    overleafID = m.group(1)
    print "overleaf ID found:", overleafID
    giturl = "https://git.overleaf.com/"+overleafID
    gitdir = './'+overleafID  
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
        subprocess.call("ls")
        os.chdir(cwd)
        print "pulled"
    lspdir = LSPDir(os.path.join(gitdir,'chapters'))
    print "checking %s" % ' '.join([f for f in lspdir.texfiles+lspdir.bibfiles])
    lspdir.check()
    lspdir.printErrors()