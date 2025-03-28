"""
Perform sanity checks for Latex files in a git repository
"""

import re
import git
import os
import sys
import subprocess


from langsci.latex.sanity import SanityDir


def cloneorpull(url, token=None):
    """
    Make a git repository available locally.

    The repo is cloned if not already available locally, otherwise, it is pull'ed.

    args:
      url (str): the url string of the repository. It can be either the html URL or the git url

    returns
      str: the file path to the local repo

    """

    if "langsci" in url:
        m = re.search("langsci/([0-9]{2,}a?)", url)
        githubID = m.group(1)
        print("GitHub ID found:", githubID)
        git_url = "https://github.com/langsci/%s.git" % githubID
        git_dir = os.path.join(os.getcwd(), githubID)
        print("git repo is ", git_url)
        try:
            git.Repo.clone_from(git_url, git_dir)
            print("cloned")
        except git.exc.GitCommandError:
            print("repo already in file system. Pulling")
            cwd = os.getcwd()
            print(git_dir)
            os.chdir(git_dir)
            subprocess.call(["git", "pull"])
            os.chdir(cwd)
            print("pulled")
    elif "overleaf" in url:
        m = re.search("overleaf.com/([0-9a-f]+)", url)
        overleaf_id = m.group(1)
        print("Overleaf ID found:", overleaf_id)
        git_url = f"https://git:{token}@git.overleaf.com/{overleaf_id}"
        print(git_url)
        git_dir = os.path.join(os.getcwd(), overleaf_id)
        print("git repo is ", git_url)
        if not os.path.exists(overleaf_id):
            subprocess.call(["git", "clone", git_url])
        else:
            print("repo already in file system. Pulling")
            cwd = os.getcwd()
            print(git_dir)
            os.chdir(git_dir)
            subprocess.call(["git", "pull"])
            os.chdir(cwd)
            print("pulled")
    return git_dir


if __name__ == "__main__":
    """
    usage:
        python3 sanitygit.py https://www.github.com/langsci/42
    """
    git_url = sys.argv[1]
    try:
        token = sys.argv[2]
    except IndexError:
        token = None
    ignorecodes = []
    # try:
    #     ignorecodes = sys.argv[2:]
    # except IndexError:
    #     pass
    d = cloneorpull(git_url, token = token)
    lspdir = SanityDir(os.path.join(d, "."), ignorecodes)
    print(
        "checking %s"
        % "\n  ".join([""] + [f for f in lspdir.texfiles + lspdir.bibfiles])
    )
    lspdir.check()
    lspdir.printErrors()
    imgdir = SanityDir(os.path.join(d, "figures"), ignorecodes)
    imgdir.check()
    imgdir.printErrors()
