# Boost (C++ Libraries)

_Boost provides free peer-reviewed portable C++ source libraries._

- Home: https://www.boost.org/
- Media: <https://en.wikipedia.org/wiki/Boost_(C%2B%2B_libraries)>
- State: mature
- Download: https://www.boost.org/users/download/
- Keywords: library
- Code repository: https://github.com/boostorg/boost.git
- Code language: C++
- Code license: Boost-1.0

[Boost Software License 1.0](https://github.com/boostorg/boost/blob/master/LICENSE_1_0.txt)

## Building

Uses its own Build process

2017-11 (1.65.1)
- Much is header only, but some parts require building
- Follow [Getting started on Windows](https://www.boost.org/doc/libs/1_65_1/more/getting_started/windows.html) or [Getting started on Unix variants](https://www.boost.org/doc/libs/1_65_1/more/getting_started/unix-variants.html)
- Building on Windows with MSVC 2017 requires a workaround (see [issue #13197](https://svn.boost.org/trac10/ticket/13197))
- With MSVC 2015 run "bootstrap vc14" followed by "b2 toolset=msvc-14.0 stage"