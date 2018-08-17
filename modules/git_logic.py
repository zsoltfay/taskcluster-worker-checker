from git import Repo

repo_url = ".."
simplified_repo_url = "https://github.com/Akhliskun/firefox-infra-changelog"


repo = Repo(repo_url)
assert not repo.bare
git = repo.git


def git_update_repo():
    git.pull()


def git_push():
    git.add("logs/runtime.log")
    git.add("logs/linux.log")
    git.add("logs/windows.log")
    git.add("logs/macosx.log")
    git.commit("-m", "Automated Push via Script")
    git.push(repo.active_branch, "origin")