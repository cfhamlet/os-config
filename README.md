# os-config

[![Build Status](https://www.travis-ci.org/cfhamlet/os-config.svg?branch=master)](https://www.travis-ci.org/cfhamlet/os-config)
[![codecov](https://codecov.io/gh/cfhamlet/os-config/branch/master/graph/badge.svg)](https://codecov.io/gh/cfhamlet/os-config)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/os-config.svg)](https://pypi.python.org/pypi/os-config)
[![PyPI](https://img.shields.io/pypi/v/os-config.svg)](https://pypi.python.org/pypi/os-config)


Config utility.

In python world, it is common to use an object as config. But normal object lacks of some useful features for config purpose. This library offers an ``Config`` object which support create, update, attribute access, etc. Consider the usability and complexity in real programming work, config attribute types are limited into: ``int``, ``long``, ``float``, ``NoneType``, ``bool``, ``str``, ``unicode``, ``tuple`` and ``Config``.
 

# Install

`pip install os-config`

# Usage

* create an empty config
```
from os_config import Config
config = Config.create()
```

* create from params
```
config = Config.create(a=1, b=2)
assert config.a == 1
assert config.b == 2
```

* create from dict
```
config = Config.create_from_dict({'a':1, 'b':2})
```

* create from json
```
json_string = '{"a": 1, "b": 2}'
config = Config.create_from_json(json_string)
```


* update from another config/dict
```
config1 = Config.create(a=1)
config2 = Config.create(a=2, b=3)
config2.update(config1)
```


# Unit Tests

`$ tox`

# License

MIT licensed.
