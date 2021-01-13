# Boost (C++ Libraries)

- Home: https://www.boost.org/
- Media: https://en.wikipedia.org/wiki/Boost_(C%2B%2B_libraries)
- State: mature
- Download: https://www.boost.org/users/download/
- Keyword: library
- Code repository: https://github.com/boostorg/boost.git (@created 2013, @stars 3932, @forks 1171)
- Code language: C++
- Code license: Boost-1.0
- Developer: Aaron Windsor, Abel Sinkovics, Alexander Nasonov, Alisdair Meredith, Andrew Sutton, Andrey Semashev, Andrii Sydorchuk, Andy Tompkins, Antony Polukhin, Artyom Beilis, Barend Gehrels, Beman Dawes, boost-commitbot, Bryce Adelstein Lelbach aka wash, burbelgruff, chhenning, chriskohlhoff, Christopher Currie, Christopher Jefferson, cppljevans, Daniel Frey, Daniel James, Daniel Wallin, danielmarsden, Daryle Walker, Dave Abrahams, Dave Jenkins, David Bellot, David Deakins, Doug Gregor, Edward Diener, Eric Niebler, Fernando Cacciola, Frank Mori Hess, François, Gennadiy Rozental, Giovanni Bajo, Glen Fernandes, goerch, Guillaume Melquiond, Gunter Winkler, Hailin Jin, Hartmut Kaiser, henry-ch, hervebronnimann, Ion Gaztañaga, jayayedee, Jeff Garland, Jens Maurer, Jeremy G. Siek, jewillco, jhellrung, joaquintides, Joel de Guzman, Jonathan Turkanis, Jonathan Wakely, João Abecasis, Juan Carlos Arevalo Baeza, Jurko Gospodnetić, jzmaddock, Jürgen Hunold, Lorenzo Caminiti, Marshall Clow, Matias Capeletto, Matt Calabrese, Matthias Troyer, Michael Caisse, Michael Jackson, Nathan Ridge, ngedmond, Nicola Musatti, nikiml, Noel Belcourt, Oliver Kowalke, Paul A. Bristow, Paul Mensonides, Peter Dimov, Raoouul, René Ferdinand Rivera Morell, Robert Ramey, Roland, rxg, Stefan Seefeld, stevensmi, swatanabe, Thomas Heller, Thomas Witt, thorsten-ottosen, Tim Blechmann, Toon Knapen, Troy Straszheim, tschw, Vicente J. Botet Escriba, Vladimir Prus

Portable C++ source libraries.
[Boost Software License 1.0](https://github.com/boostorg/boost/blob/master/LICENSE_1_0.txt)

## Building

Uses its own Build process

2017-11 (1.65.1)
Much is header only, but some parts require building
Follow [Getting started on Windows](https://www.boost.org/doc/libs/1_65_1/more/getting_started/windows.html) or [Getting started on Unix variants](https://www.boost.org/doc/libs/1_65_1/more/getting_started/unix-variants.html)
Building on Windows with MSVC 2017 requires a workaround (see [issue #13197](https://svn.boost.org/trac10/ticket/13197))
With MSVC 2015 run "bootstrap vc14" followed by "b2 toolset=msvc-14.0 stage"
