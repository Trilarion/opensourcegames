"""
takes all gits that we have in the list and checks the master branch out, then collects some statistics:
- number of distinct comitters
- list of commit dates
- number of commits
- language detection and lines of code counting on final state

uses git log --format="%an, %at, %cn, %ct" --all ti get commits, committers and times (as unix time stamp)
"""
