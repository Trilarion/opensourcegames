"""
Uses the Github API to learn more about the Github projects.
"""

# Github
urls = [x for x in repos if x.startswith('https://github.com/')]
urls = []
for url in urls:
    print(' github repo: {}'.format(url))
    github_info = osg_github.retrieve_repo_info(url)
    for contributor in github_info['contributors']:
        name = contributor.name
        dev = developer_info_lookup(name)
        in_devs = dev and 'contact' in dev and contributor.login + '@GH' in dev['contact']
        in_entry = name in entry_developer
        if in_devs and in_entry:
            continue  # already existing in entry and devs
        content += ' {}: {}@GH'.format(name, contributor.login)
        if contributor.blog:
            content += ' url: {}'.format(contributor.blog)
        if not in_devs:
            content += ' (not in devs)'
        if not in_entry:
            content += ' (not in entry)'
        content += '\n'

if __name__ == "__main__":

