# Boost (C++ Libraries)

- Home: https://www.boost.org/
- Media: https://en.wikipedia.org/wiki/Boost_(C%2B%2B_libraries)
- State: mature
- Download: https://www.boost.org/users/download/
- Keyword: library
- Code repository: https://github.com/boostorg/boost.git (@created 2013, @stars 3932, @forks 1171)
- Code language: C++
- Code license: Boost-1.0
- Developer: boost-commitbot, Vladimir Prus, Dave Abrahams, jzmaddock, Hartmut Kaiser, Jeremy G. Siek, Daniel James, Beman Dawes, Doug Gregor, Eric Niebler, René Ferdinand Rivera Morell, Joel de Guzman, Robert Ramey, Peter Dimov, Jens Maurer, Gennadiy Rozental, Jeff Garland, Jonathan Turkanis, chriskohlhoff, jewillco, joaquintides, stevensmi, swatanabe, thorsten-ottosen, Ion Gaztañaga, rxg, Jurko Gospodnetić, Vicente J. Botet Escriba, tschw, Marshall Clow, Barend Gehrels, Andrey Semashev, Daniel Wallin, Frank Mori Hess, Paul Mensonides, Paul A. Bristow, Jürgen Hunold, Fernando Cacciola, Toon Knapen, henry-ch, Alexander Nasonov, Roland, Guillaume Melquiond, Gunter Winkler, Andrew Sutton, Noel Belcourt, Thomas Witt, João Abecasis, Matthias Troyer, Troy Straszheim, Bryce Adelstein Lelbach aka wash, Daryle Walker, Antony Polukhin, danielmarsden, burbelgruff, Matias Capeletto, Oliver Kowalke, Andy Tompkins, goerch, Aaron Windsor, Alisdair Meredith, François, Nicola Musatti, Tim Blechmann, Hailin Jin, Glen Fernandes, chhenning, Daniel Frey, Stefan Seefeld, David Bellot, ngedmond, David Deakins, hervebronnimann, Christopher Currie, Dave Jenkins, Andrii Sydorchuk, Michael Jackson, Christopher Jefferson, Giovanni Bajo, jayayedee, Edward Diener, Raoouul, Artyom Beilis, Lorenzo Caminiti, Nathan Ridge, nikiml, Thomas Heller, jhellrung, Juan Carlos Arevalo Baeza, cppljevans, Matt Calabrese, Michael Caisse, Jonathan Wakely, Abel Sinkovics

Portable C++ source libraries.
[Boost Software License 1.0](https://github.com/boostorg/boost/blob/master/LICENSE_1_0.txt)

## Building

Uses its own Build process

2017-11 (1.65.1)
Much is header only, but some parts require building
Follow [Getting started on Windows](https://www.boost.org/doc/libs/1_65_1/more/getting_started/windows.html) or [Getting started on Unix variants](https://www.boost.org/doc/libs/1_65_1/more/getting_started/unix-variants.html)
Building on Windows with MSVC 2017 requires a workaround (see [issue #13197](https://svn.boost.org/trac10/ticket/13197))
With MSVC 2015 run "bootstrap vc14" followed by "b2 toolset=msvc-14.0 stage"
