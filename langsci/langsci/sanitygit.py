"""
Perform sanity checks for Latex files in a git repository
"""

from sanitycheck import SanityDir
import re
import git 
import os
import sys
import subprocess


def cloneorpull(url):
    """
    Make a git repository available locally. 
    
    The repo is cloned if not already available locally, otherwise, it is pull'ed.
    
    args:
      url (str): the url string of the repository. It can be either the html URL or the git url
      
    returns
      str: the file path to the local repo
      
    """
    m = re.search('langsci/([0-9]{2,}a?)',url)
    githubID = m.group(1)
    print("GitHub ID found:", githubID)
    giturl = "https://github.com/langsci/%s.git"%githubID
    gitdir = os.path.join(os.getcwd(),githubID)
    print("git repo is ", giturl)
    try:
        git.Repo.clone_from(giturl, gitdir)
        print("cloned")
    except git.exc.GitCommandError:
        print("repo already in file system. Pulling")
        cwd = os.getcwd()
        print(gitdir)
        os.chdir(gitdir)
        subprocess.call(["git","pull"]) 
        os.chdir(cwd)
        print("pulled")
    return gitdir 
    
    
if __name__ == "__main__":
    githuburl = sys.argv[1]
    d = cloneorpull(githuburl)
    lspdir = SanityDir(os.path.join(d,'chapters'))
    print("checking %s" % ' '.join([f for f in lspdir.texfiles+lspdir.bibfiles]))
    lspdir.check()
    lspdir.printErrors()
    imgdir =  SanityDir(os.path.join(d,'figures'))
    imgdir.check()
    imgdir.printErrors()
    