# leankit

[![NPM info](https://travis-ci.org/Funk66/leankit.svg?branch=master)](https://travis-ci.org/Funk66/leankit.svg?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3976597cd3694ccba012c1da176fa85f)](https://www.codacy.com/app/Funk66/leankit?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Funk66/leankit&amp;utm_campaign=Badge_Grade)

Python wrapper for Leankit's API v1.0

## Installation

  ```
  pip install leankit
  ```

## Usage

First you need to authenticate the client by providing your leankit domain, username and password.
After that, you can download a board by simply instantiating the `leankit.Board` class with its id as only parameter.

  ```python
  import leankit
  leankit.api.authenticate('domain', 'user@example.org', 'passw0rd')
  board = leankit.Board(123456789)
  ```

The different board elements will be arranged in dictionaries and made available as attributes of the board object.

## Contributing

In lieu of a formal style guide, take care to maintain the existing coding style.
Add unit tests for any new or changed functionality. Lint and test your code.
