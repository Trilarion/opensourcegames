# Contribution guidelines

There are two main ways to contribute content to the OSGL.

### 1. New issue on the [Issue tracker](https://github.com/Trilarion/opensourcegames/issues)

Recommended if you have only small changes to entries or if you have changes in developer or inspiration informations
or if you are not familiar with pull requests.

Please create one issue for each entry that is to be modified/added and provide all the information that is required to
update or create a new entry.

Exception: For reporting screenshot URLs, please use [this issue]().

### 2. Fork the repository and submit a pull request

Recommended if you have many changes and are familiar with pull requests. Please study carefully the information below.

### Requirements for a adding a new entry

A new entry can be created if

- it's about a game, a game maker/editor, a game tool, a framework/engine/library primarily used in games
- features a FOSS license (GPL, MIT, ...) of the code and the code must be publicly available
- a game must be at least in beta (with an executable demo)
- if it's not a game, popularity should be high enough that it is somewhat notable (I'll have to decide on that)

Irrelevant are activity status, the location of the code, or the existence of an inspiration.

### Format of entries

All entries are stored as [markdown](https://en.wikipedia.org/wiki/Markdown) text with some specific conventions in the
[entries](entries) folder. Adding a new entry is as easy as modifying the [template](template.md) and adding the modified
markdown file the [entries](entries) folder. Please observe all conventions stated below.

*Note: Outside of the [entries](entries) folder, no file needs to be changed if the goal of a contribution is to change content only!*

Description of the fields in the [template](template.md). Comments start with "//".

<pre>
# {NAME}  // name of the game

- Home: {URL}   // project main site(s) (most significant first)
- Media: {URL}  // (optional) links to wikipedia and other significant mentions
- Inspiration: {XX}  // (optional) names of games used as inspiration for this entry
- State: {XX}   // one of {beta, mature}, (optional) "inactive since YEAR"
- Play: {URL}   // (optional) link(s) to online play possibilities
- Download: {URL}   // (optional) link(s) to download binary (or source if no repository is given) releases
- Platform: {XX}    // (optional) list of supported platforms {Windows, Linux, macOS, Android, iOS, Web}
- Keyword: {XX}     // list of tags describing the game, first tage is the main category tag, at least one category tag needed
- Code repository: {URL}  // code repositories (most significant first)
- Code language: {XX}     // programming language(s) used
- Code license: {XX}      // license of the code, use "Custom" with comment in () if the license is project-specific
- Code dependency: {XX}   // (optional) important third party libraries / frameworks used by the project
- Assets license: {XX}    // (optional) license(s) of the assets (artwork, ..)
- Developer: {XX}         // (optional) list of developer names

Notes // whatever you want to put up here, focused on the technical aspects

## Building

- Build system: {XX}       // (optional) typically one of {CMake, Autoconf, Gradle, ..} but can be more
- Build instruction: {XX}  // (optional) link(s) to build instructions offered by the project

Notes // addition build instructions or technical comments you want to put here
</pre>

### Important conventions (please read carefully!)

- For the name of an entry file, use the name of the game, convert to lower case and replace spaces with underlines.
  Example: "Alex the Allegator 4" is in file alex_the_allegator_4.md. In the case of a name collision just add something
  to make file names unique.
- If there are multiple links, licenses, ... separate them by comma.
- The same link can be assigned to different fields (home could also be the code repository, etc.).
- Put comments in "()" parentheses after each values.
- Remove lines with fields that do not apply to the project or where information is not available otherwise.
- Status active is implied/default unless the optional "inactive since" is present
- All lines starting with '- ' are considered fields.
- No need to add the number of stars/forks/founding year of Git repositories (GitHub, GitLab), that is done automatically regularly
- No need to add or change any text starting with "@", unless you really know what to do.
- No need to modify "code/archives.json", that will be overwritten regularly.
- No need to modify "docs/**" or "entries/screenshots/*" or "entries/tocs/*"

### Developer information

The developer information relates developers to open source games they have participated in. Developer profiles on GitHub,
SourceForge or BitBucket are linked on a developer information and also on the game entries in the developers field.
The relation between developers and games is shown twice to allow for both search directions, i.e. find all developers of
a game or all games of a developer. A consistency check will run regularly on the content and will give precedence to
the developer names stored in the games entries (the games list stored in the developer information will be overwritten).

It is recommended to suggest changes to developer information within an issue on the issue tracker although it's also
possible to modify the [developers file](developers.md), if you know what you are doing. Please add missing developers only
to the "Developer" field in an entry.

### Inspiration information

Inspirations are short pieces of information that collect links to inspirations website or Wikipedia websites and also
link to all entries that have this game as inspiration. Please only edit entries "Inspiration" fields to indicate that a
game has a certain inspiration.  If not sure, suggest changes or additions to inspirations within an issue at the issue
tracker (see above).

### Updates to the code base

All Python scripts reside in the code folder, their purpose is:

- checking consistency of the contained entry, developer and inspiration information (maintenance_xxx.py)
- reading and writing markdown files from and to Python dictionaries (with lark grammars *.lark)
- keep a local set of git repositories of the games (archive_update.py)
- synchronize with opensourcegameclones and LibreGameWiki (synchronization/*.py)
- generate the static website that is stored in doc/* (code/html/generate_static_website.py via *.jinja templates)

Help: [MarkDown Help](https://help.github.com/articles/github-flavored-markdown), [Markdown Cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)