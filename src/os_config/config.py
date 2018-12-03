import sys
import json
import operator

_PY3 = sys.version_info[0] == 3
if _PY3:
    iteritems = operator.methodcaller('items')
else:
    iteritems = operator.methodcaller("iteritems")


class _Config(object):

    def __setattr__(self, key, value):
        if key.startswith('_'):
            raise AttributeError("Attribute key not allowed startswith '_'")

        if not isinstance(value, VALID_TYPES):
            raise AttributeError('Do not support %r' % type(value))

        self.__dict__[key] = value

    def __iter__(self):
        return iter([(k, v) for k, v in iteritems(self.__dict__) if not k.startswith('_')])

    def __contains__(self, key):
        return key in self.__dict__

    def update(self, o):
        if isinstance(o, _Config):
            for k, v in o:
                if k not in self:
                    setattr(self, k, v)
                elif isinstance(getattr(self, k), _Config):
                    if isinstance(v, _Config):
                        getattr(self, k).update(v)
                    else:
                        self.k = v
        elif isinstance(o, dict):
            if not o:
                return
            c = Config.create()
            for k, v in iteritems(o):
                if isinstance(v, dict):
                    v = Config.create_from_dict(v)
                setattr(c, k, v)
            self.update(c)


class Config(object):

    def __new__(cls, *args, **kwargs):
        raise TypeError('Not allowed create directly')

    @classmethod
    def create(cls, **kwargs):
        c = _Config()
        c.update(kwargs)
        return c

    @classmethod
    def create_from_dict(cls, d):
        assert isinstance(d, dict)
        return Config.create(**d)


VALID_TYPES = [_Config, int, tuple]


if _PY3:
    VALID_TYPES.extend([str,  bytes])
else:
    VALID_TYPES.extend([basestring, long, unicode])

VALID_TYPES = tuple(VALID_TYPES)
