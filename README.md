# leankit

[![NPM info](https://travis-ci.org/Funk66/leankit.svg?branch=master)](https://travis-ci.org/Funk66/leankit.svg?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3976597cd3694ccba012c1da176fa85f)](https://www.codacy.com/app/Funk66/leankit?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Funk66/leankit&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/3976597cd3694ccba012c1da176fa85f)](https://www.codacy.com/app/Funk66/leankit?utm_source=github.com&utm_medium=referral&utm_content=Funk66/leankit&utm_campaign=Badge_Coverage)

Python 3.x wrapper for Leankit's API v1.0

## Installation

  ```bash
  $ pip install leankit
  ```

## Usage

First you need to authenticate the client by providing your leankit domain, username and password.

  ```python
  >>> import leankit
  >>> leankit.api.authenticate('domain', 'user@example.org', 'passw0rd')
  ```

You can skip this step by setting the environment variables `LEANKIT_DOMAIN`, `LEANKIT_USERNAME` and `LEANKIT_PASSWORD` respectively.
Alternatively, credentials can be stored in plain text within your `~/.config` folder with the following command:

  ```bash
  $ python -m leankit.config
  ```

The configuration file has preference over the environment variables.

To download a board, simply instantiate the `leankit.Board` class with the board id as only parameter.

  ```python
  >>> board = leankit.Board(123456789)
  ```

The different board elements will be arranged in dictionaries and made available as attributes of the board object.
Kanban elements can be treated both as dictionaries and as objects with snake case attributes.
Dates are converted to native objects automatically for convenience.

  ```python
  >>> card = board.cards[987654321]
  >>> card['DateArchived']
  datetime.date(2017, 5, 23)
  >>> card.date_archived
  datetime.date(2017, 5, 23)
  >>> card.assigned_user.email_address
  user@example.org
  ```

The history of each card is downloaded and cached when the `history` attribute is accessed for the first time.

To access the data as received from the API, use the `raw_data` attribute.

  ```python
  >>> board.card_types[123123123].raw_data
  {'ColorHex': '#d3e0e4',
   'IconColor': None,
   'IconName': None,
   'IconPath': None,
   'Id': 123123123,
   'IsCardType': True,
   'IsDefault': False,
   'IsDefaultTaskType': False,
   'IsTaskType': True,
   'Name': 'Improvement'}
  ```

## Testing

Additionally to unit tests, there are some integration tests to ensure that the data received from Leankit's API
is correct and have the expected format. Integration tests may take a while to complete, depending on the size
of the board tested, so they are deactivated by default. 

## Contributing

In lieu of a formal style guide, take care to maintain the existing coding style.
Add unit tests for any new or changed functionality. Lint and test your code.
