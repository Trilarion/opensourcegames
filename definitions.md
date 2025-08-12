# Definitions of field names and content

This file explains the meaning and possible values for the content of this list, i.e. the games, the developers, the inspirations, ..

## Game

For each game, tool for games or framework to create games there is a single *.md
file in the entries folder. The structure of a game is shortly defined in
template.md and in more detail here. In the following each part of a game entry
is explained. Please note that the content of each field is filled in to the best
of our knowledge, but often involves also some guesswork (for example which platforms
are supported or if the game is beta or rather mature is subjective and often difficult
to judge especially without binaries). Updates are always welcome.

Incomplete information: It's understood that relevant information can be missing from game entries,
i.e. that the information given in a game entry is in general correct but not exhaustive. The expectation is
a future update can always provide the missing information.

Developer info: The grammar to parse an entry programmatically is in code/grammar_entries.lark

### Name

On the first line of the game entry should be the official name of the game as written
by the developers of the game on their homepage, including capitalization.

Developer info: the name the game entry file is derived from the game name. See code/utils/osg.py/canonical_name()

### Home

This field is mandatory and contains a list of URLs with at least one entry. The URLs in this
list should contain important game website addresses (not download or repository pages) with
the most important first. If a project has only a repository, the URL of the repository website (without .git) should be given. If project sites are not available anymore, links to the web-archive are appreciated. If newer sites exist, older home addresses can be marked with
the annotation (@old). All URLs not marked @old will be shown in the HTML rendering.

Developer info: Annotations are flags in parentheses after content starting with @. Some fields allow them, others not.

### Media

This field is optional and contains a list of URLs with at least one entry if the field is present.
The URLs are links to news reports (articles on games websites, Wikipedia, ..) that are not by
the project owners itself, but feature the project.

### Inspiration

This field is optional and contains a list of names with at least one entry if the field is present.
Names can be names of other games in this list or names of famous other games. It's important
to always write the names of inspirations in the same way.

Developer info: Script maintenance_inspirations allows (among others) to search for similar written names.

### State

This field is mandatory and contains one of {"beta", "mature"} for games that a playable but
not yet finished (beta) or quite finished (mature). We want to limit entries to those that
feature at least some gameplay. Mature implies a more complete and polished game experience
than beta. Versioning of the game (0.X vs. 1.X) may be used to determine the state.
Additionally, if the source code of the game has not seen any update since at least
one year, we mark it as inactive and add "inactive since YYYY" with a comma to the state.

### Play

This field is optional and contain one URL. If the game supports playing it in the browser and
there is a website that allows playing it, this field will contain the address to this site.

### Download

This field is optional and contains a list of one or more URLs. The first URL is supposed to be
the main address for downloads of binary distributions. Typically it will be the address of a
download link on the home page or a link to a GitHub releases page or a link to a download
center somewhere else.

### Keyword

This field is mandatory and contains a list of keywords with at least one essential keyword and
arbitrarily many other keywords. A combination of keywords means that they all apply (example action, adventure).
The most often used keywords (see also statistics.md) are explained as follows:

Essential keywords

- action: Games that require quick reflexes, coordination and offers fast-paced gameplay. Often combat oriented.
- arcade: Games that emulate fast-paced, score-driven gameplay of traditional arcade machines featuring simple controls and short sessions.
- adventure: Games that focus on narrative-driven gameplay, where players explore environments, solve puzzles and interact with other characters to progress through a story.
- visual novel: Interactive, narrative game that focuses on storytelling through text and visuals, often offering players choices that influence the plot.
- sports: Games that simulate real sport-events, allowing players to control athletes or teams to compete in matches, often emphasizing skill, strategy and action.
- platform: Games that focus on navigating a character through levels by jumping between platforms, avoiding obstacles and defeating enemies by precisely timed movement.
- puzzle: Game that challenge players to solve logic-based puzzles, riddles or spatial challenges, often requiring strategic thinking to progress.
- role playing: Games where players assume the role of characters in a fictional world, making decisions that influence the story and character development.
- simulations: Games that mimic real-world systems, allowing players to control and manage many aspects of the environment with a focus on realism and strategic decision-making.
- strategy: Games where players must plan and make short-/longterm decisions to achieve victory often including resource management and unit control.
- cards: Games that simulate (traditional) card games, where players strategize by drawing, playing and managing cards to achieve specific objectives.
- board: Games that simulate (traditional) board games, where players take turns to move pieces, manage resources or complete objectives on a virtual board.
- music: Games that allow players to interact with rhythm or melody based gameplay, requiring them to match musical patterns through timed inputs.
- educational: Games that aim to teach specific skills or knowledge through interactive gameplay, combining learning objectives and recreation to make education more effective or enjoyable.
- tool: Application that assists players in playing other games or that assists game creators with non-programming content creation.
- game engine: Core software architecture that handles main functionality and mechanics of a video game.
- framework: Suite of libraries, that provide developers with tools, libraries and reusable components needed in the creation of video games handling commonly used tasks.
- library: Collection of pre-written code that developers can use to perform specific tasks bundled in one project.
- remake: New version of an existing game that remains as closely as possible to the original gameplay mechanics but may improve on audio and visuals or improve compatibility with modern platforms.

Other popular keywords

- content: Status of the artwork (sound, graphics, ..) of the game, which may be under different licenses or not freely available than the code.
- clone: Game that is inspired by an existing game and may show similar gameplay and audiovisuals, but may also deviate somewhat from the original's narrative.
- shooter: Action game focused on combat with ranged weapons.
- 2D/3D: Dimensional representation of game objects with either flat visuals (2D) or having depth (3D) for more realistic representations.
- turn-based/real-time: Turn-based gameplay allows players to sequentially take longer time to make decisions while in real-time gameplay all players make decisions and take actions simultaneously, often under considerable time pressure.
- space: Games that take place in outer-space often featuring exploration and resource management.
- first-person: Games that represent gameplay from the player's perspective, allowing them to experience the game world through the eyes of the character they control.
- skill: Games that emphasize muscular abilities requiring precision, timing and quick reflexes.
- roguelike: Clones of the dungeon crawling game rogue from around 1980, characterized by procedural world generation, turn-based movement and permanent death.
- racing: Sports game where players compete in timed matches using various vehicles like cars, boats emphasizing speed and skillful maneuvering.
- text-based: Games with input and output only through a text console.
- side-scrolling: Games that involve navigating a character or object across a 2D environment that moves horizontally or vertically only.
- flight: Games that simulate flying aircraft.
- top-down: Games where the gameplay is viewed from a bird's-eye perspective allowing players to control characters or objects in a 2D environment.
- official: A game whose code base has been released by the original commercial publisher
- 4X: Strategy games characterized by four key elements: eXplore, eXpand, eXploit, and eXterminate.

Developer info: Essential and interesting keywords are defined in code/utils/constants.py. They
will be used as categories in the HTML rendering.

### Code repository

List of addresses of source code repositories, where the source code for the game is stored together with a history and author information.
The actual checkout/clone addresses should be provided, i.e. ending on ".git" for a git repository on GitHub, .... For SVN, the top level
directory should be given. Multiple repositories can be listed, implying that the first one is the most important one. Meta information
can be given in parentheses. Significant meta information is given in annotations.

Developer info: Annotations start with "@".

### Code language

Designates all the major used programming languages for the project. The threshold for significance is 2-3% when statistics
about programming languages are given (GitHub or GitLab do that, probably number of lines based). Typically only the most general
name of each dialect is used, i.e. Pascal instead of Delphi Pascal, Basic instead of Blitz Basic. CSS or GLSL are not seen
as programming languages here.

Developer info: See constants/language_urls (can be extended) for spelling of languages.

### Code license

List of all licenses the code is under from a set of known open source licenses. If a custom license is used that is
unlikely to be used elsewhere the license is named "custom". Ideally there would be a link to the license information file
in the additional information in parentheses.

Developer info: See constants/known_licenses and constants/license_urls_repo for spelling of licenses.

### Code dependency

List of some of the major code dependencies that are gaming relevant, i.e. SDL or pygame and many more. This list should
by no means be exhaustive and just list relevant dependencies. There is no list of relevant dependencies yet.

### Assets license

List of all licenses the non-code content (artwork) of the game is under. Also applies if only part of the artwork is under
these licenses (can be specified in additional information in parentheses). If the whole content is under open source
licenses, a keyword "content open" should be added to field "Keyword". If the content is proprietary, the keyword
"content proprietary" should be added.

### Developer

List of all significant (yet to be determined) developers of a project in a form how they identify themselves. With
GitHub, GitLab or SourceForge, developer names are the developer account names and are taken from the interface.
In other cases, names can be taken from source repository commit messages or from readme files / copyright notices in
projects. This list can easily be incomplete, but also contain duplicate names for a single developer.

### Notes

Usage is a bit unclear currently. Typically contains a single line of information with some additional information
or a summary of the project. Can be an arbitrary amount of text excluding "#" at the beginning of a line.

### Building

No user input required here. The "## Building" means that a specific section in the entry about creation of binaries
for an entry is following.

### Build system

List of build systems used. If no build system is detectable, this field can be left out of the entry.

### Build instruction

Link to build instructions. If no such link is detectable, this field can be left out of the entry.

## Inspiration

A list of games that serve as inspiration for the open source games here. Additional information about the inspirations
is collected in file inspirations.md and used to render an inspirations page on the website. An inspiration has the
following fields and meanings.

### Name

The name of the inspiration and the number of inspired entries in brackets.

### Inspired entries

A list of inspired entries. Must be the names of existing entries.

### Media

List of lists for further general information about the inspiration like homepages, wikipedia articles.

### Included

Contains "Yes" if the inspiration is itself an open source game that is included in the list.

## Developer

A list of developers that are listed as creators of the open source games here. Additional information about the
developer is collected here.

Developer info: Partly unsolved problem: developer names are not unique.

### Name

Name of the developer as it appears in the Developer field in a game entry with the number of games in brackets.

### Games

List of open source games names that the developer contributed to.

### Contact

Abbreviated list of links to developer profiles. Profiles at GitHub are abbreviated with username@GH and the same for
GitLab (@GL), SourForge (@SF) and maybe others.

### Home

List of links to developer homepages.

## Screenshots

Screenshots are stored in folder "entries/screenshots". Screenshots are small (height 128 pixels, 70% jpg quality) files
with a specific naming [name of the entry file]_01/02/03.jpg. There can be maximally 3 screenshots. The screenshots are
also listed in "entries/screenshots/README.md" possibly with links to the original screenshots which will be used as link
targets. If the original screenshot is not much larger anyway the link is prefixed by "!" and used as proof of origin but
not as a link target.

Screenshots should show gameplay, not logos. A list of rejected screenshots that should not be used is in "entries/screenshots/rejected.txt".

## Rejected

Some frequently found or proposed game projects do not qualify for this list, in particular those without clear license information.
In "code/rejected.txt" as list of projects not included is given. The format is "name (links): reason for rejection".