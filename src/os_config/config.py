import ast
import json
import operator
import sys
import types

_PY3 = sys.version_info[0] == 3
if _PY3:
    iteritems = operator.methodcaller('items')
else:
    iteritems = operator.methodcaller("iteritems")


def valid_variable_name(name):
    try:
        ast.parse('{} = None'.format(name))
        return True
    except (SyntaxError, ValueError, TypeError):
        return False


PROTECTED_ATTRIBUTE_NAMES = set(['_Config__sub_configs'])


class _Config(object):

    def __init__(self):
        self.__sub_configs = set([self, ])

    def __is_sub_config(self, c):
        for sub in self.__sub_configs:
            if c == sub:
                return True
            elif sub == self:
                continue
            elif sub.__is_sub_config(c):
                return True
        return False

    def __ensure_not_sub_config_of(self, c):
        if c.__is_sub_config(self):
            raise AttributeError('Can not assign recursively')

    def __ensure_attribute_name(self, key):
        if key in PROTECTED_ATTRIBUTE_NAMES:
            return

        if key.startswith('_'):
            raise AttributeError(
                "Attribute key not allowed startswith '_', %s" % str(key))

        elif not valid_variable_name(key):
            raise AttributeError("Invalid attribute name %s" % str(key))

    def __ensure_attribute_type(self, value):

        if not isinstance(value, VALID_TYPES):
            raise AttributeError('Do not support %r' % type(value))

    def __add_sub_config(self, c):
        if isinstance(c, _Config):
            self.__sub_configs.add(c)
        elif isinstance(c, tuple):
            for t in c:
                self.__add_sub_config(t)

    def __discard_sub_config(self, c):
        if c in self.__sub_configs:
            self.__sub_configs.discard(c)
        if isinstance(c, tuple):
            for t in c:
                self.__discard_sub_config(t)

    def __assign_config_obj(self, key, value):
        self.__ensure_not_sub_config_of(value)
        self.__add_sub_config(value)
        self.__assign(key, value)

    def __assign_tuple_obj(self, key, value):

        sub_configs = set()
        objs = [value]
        while len(objs) > 0:
            obj = objs.pop()
            if isinstance(obj, _Config):
                self.__ensure_not_sub_config_of(obj)
                sub_configs.add(obj)
            elif isinstance(obj, tuple):
                objs.extend(obj)
        self.__sub_configs.update(sub_configs)
        self.__assign(key, value)

    def __assign(self, key, value):
        if key in self.__dict__:
            v = self.__dict__[key]
            if v != value:
                self.__discard_sub_config(v)
        self.__dict__[key] = value

    def __setattr__(self, key, value):
        self.__ensure_attribute_name(key)
        if key not in PROTECTED_ATTRIBUTE_NAMES:
            self.__ensure_attribute_type(value)
        if isinstance(value, _Config):
            self.__assign_config_obj(key, value)
        elif isinstance(value, tuple):
            self.__assign_tuple_obj(key, value)
        else:
            self.__assign(key, value)

    def __iter__(self):
        return iter([(k, v) for k, v in iteritems(self.__dict__) if not k.startswith('_')])

    def __contains__(self, key):
        return key in self.__dict__

    def __update_from_config(self, o):
        self.__ensure_not_sub_config_of(o)
        o.__ensure_not_sub_config_of(self)

        for k, v in o:
            if k not in self:
                setattr(self, k, v)
                continue
            else:
                vv = getattr(self, k)
                if isinstance(v, _Config) and isinstance(vv, _Config):
                    vv.update(v)
                else:
                    setattr(self, k, v)

    def __update_from_dict(self, d):
        if not d:
            return
        t = Config.create()
        for k, v in iteritems(d):
            if isinstance(v, dict):
                vv = Config.create()
                vv.update(v)
                setattr(t, k, vv)
            else:
                setattr(t, k, v)

        self.update(t)

    def update(self, o):
        if isinstance(o, _Config):
            self.__update_from_config(o)
        elif isinstance(o, dict):
            self.__update_from_dict(o)
        else:
            raise ValueError('Can not update from %s' % str(type(o)))


class _ConfigEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, _Config):
            return dict([(k, v) for k, v in o])
        return super(_ConfigEncoder, self).default(o)


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
        if not isinstance(d, dict):
            raise TypeError('Not dict, %s' % type(d))
        return Config.create(**d)

    @classmethod
    def create_from_json(cls, j):
        d = json.loads(j)
        return Config.create_from_dict(d)

    @classmethod
    def to_json(cls, c):
        return json.dumps(c, cls=_ConfigEncoder)


VALID_TYPES = [_Config, int, tuple, type(None), bool, float]


if _PY3:
    VALID_TYPES.extend([str,  bytes])
    string_types = str,
else:
    VALID_TYPES.extend([basestring, long, unicode])
    string_types = basestring

VALID_TYPES = tuple(VALID_TYPES)
