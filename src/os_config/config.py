import ast
import json
import operator
import sys
import types
from collections import Counter


_PY3 = sys.version_info[0] == 3
if _PY3:
    iteritems = operator.methodcaller('items')
else:
    iteritems = operator.methodcaller("iteritems")


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass from six."""

    class metaclass(type):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)

        @classmethod
        def __prepare__(cls, name, this_bases):
            return meta.__prepare__(name, bases)
    return type.__new__(metaclass, 'temporary_class', (), {})


def valid_variable_name(name):
    try:
        ast.parse('{} = None'.format(name))
        return True
    except (SyntaxError, ValueError, TypeError):
        return False


class ConfigMeta(type):
    def __new__(cls, name, bases, namespace):
        def not_allowed(self):
            raise TypeError('Cannot init directly')

        true_init = namespace.get('__init__')
        namespace['__init__'] = not_allowed

        def create(cls, **kwargs):
            c = cls.__new__(cls)
            true_init(c)
            Config.update(c, kwargs)
            return c

        namespace['create'] = classmethod(create)

        return super(ConfigMeta, cls).__new__(cls, name, bases, namespace)


class Config(with_metaclass(ConfigMeta, object)):

    def __init__(self):
        self.__dict__['_Config__dict'] = {}
        self.__dict__['_Config__sub_configs'] = Counter({self: 1})

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

        if key.startswith('_'):
            raise AttributeError(
                "Attribute key not allowed startswith '_', %s" % str(key))

        elif not valid_variable_name(key):
            raise AttributeError("Invalid attribute name %s" % str(key))

        return True

    def __ensure_attribute_type(self, value):

        if not isinstance(value, VALID_TYPES):
            raise AttributeError('Do not support %r' % type(value))

    def __repr__(self):
        return repr(self.__dict)

    def __discard_sub_config(self, c):
        if c in self.__sub_configs:
            self.__sub_configs[c] -= 1
            if self.__sub_configs[c] <= 0:
                self.__sub_configs.pop(c)
        if isinstance(c, tuple):
            for t in c:
                self.__discard_sub_config(t)

    def __assign_config_obj(self, key, value):
        self.__ensure_not_sub_config_of(value)
        self.__sub_configs[value] += 1
        self.__assign(key, value)

    def __true_tuple(self, sub_configs, tp):
        lst = []
        for obj in tp:
            if isinstance(obj, (list, tuple)):
                lst.append(self.__true_tuple(sub_configs, obj))
                continue
            elif isinstance(obj, dict):
                obj = Config.from_dict(obj)

            if isinstance(obj, Config):
                self.__ensure_not_sub_config_of(obj)
                sub_configs[obj] += 1
            else:
                self.__ensure_attribute_type(obj)
            lst.append(obj)

        return tuple(lst)

    def __assign_tuple_obj(self, key, value):

        sub_configs = Counter()
        new_value = self.__true_tuple(sub_configs, value)
        self.__sub_configs.update(sub_configs)
        self.__assign(key, new_value)

    def __assign(self, key, value):
        if key in self.__dict:
            v = self.__dict[key]
            if v != value:
                self.__discard_sub_config(v)
        self.__dict[key] = value

    def __setattr__(self, key, value):
        if not self.__ensure_attribute_name(key):
            return
        if isinstance(value, list):
            value = tuple(value)
        elif isinstance(value, dict):
            value = Config.from_dict(value)

        self.__ensure_attribute_type(value)

        if isinstance(value, Config):
            self.__assign_config_obj(key, value)
        elif isinstance(value, tuple):
            self.__assign_tuple_obj(key, value)
        else:
            self.__assign(key, value)

    def __getattr__(self, key):
        if key not in self.__dict:
            raise AttributeError('Do not have attribute \'{}\''.format(key))
        return self.__dict[key]

    def __len__(self):
        return len(self.__dict)

    def __iter__(self):
        return iter([(k, v) for k, v in iteritems(self.__dict) if not k.startswith('_')])

    def __contains__(self, key):
        return key in self.__dict

    def __update_from_config(self, o):
        self.__ensure_not_sub_config_of(o)
        o.__ensure_not_sub_config_of(self)

        for k, v in o:
            if k not in self:
                setattr(self, k, v)
            else:
                vv = getattr(self, k)
                if isinstance(v, Config) and isinstance(vv, Config):
                    Config.update(vv, v)
                else:
                    setattr(self, k, v)

    def __update_from_dict(self, d):
        if not d:
            return
        t = Config.create()
        for k, v in iteritems(d):
            if isinstance(v, dict):
                vv = Config.create()
                Config.update(vv, v)
                setattr(t, k, vv)
            else:
                setattr(t, k, v)

        self.__update(t)

    def __update(self, o):
        if isinstance(o, Config):
            self.__update_from_config(o)
        elif isinstance(o, dict):
            self.__update_from_dict(o)
        else:
            raise ValueError('Can not update from %s' % str(type(o)))

    def __pop(self,  key):
        if key in self.__dict:
            v = self.__dict[key]
            self.__discard_sub_config(v)

        self.__dict.pop(key)

    def __get(self, key, default=None):
        return self.__dict.get(key, default)

    @classmethod
    def get(cls, c, key, default=None):
        assert isinstance(c, Config)
        return c._Config__get(key, default)

    @classmethod
    def pop(cls, c, key):
        assert isinstance(c, Config)
        return c._Config__pop(key)

    @classmethod
    def update(cls, c, o):
        assert isinstance(c, Config)
        c._Config__update(o)

    @classmethod
    def from_pyfile(cls, filename):
        module = types.ModuleType('config')
        module.__file__ = filename
        try:
            with open(filename) as config_file:
                exec(compile(config_file.read(), filename, 'exec'),
                     module.__dict__)
        except IOError as e:
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
        return cls.from_object(module)

    @classmethod
    def from_object(cls, obj):
        d = {}
        for key in dir(obj):
            if key.startswith('_'):
                continue
            d[key] = getattr(obj, key)
        return cls.from_dict(d)

    @classmethod
    def from_json(cls, j):
        d = json.loads(j)
        return cls.from_dict(d)

    @classmethod
    def from_dict(cls, d):
        assert isinstance(d, dict)
        return cls.create(**d)

    @classmethod
    def to_json(cls, c, **kwargs):
        cls = _ConfigEncoder
        if 'cls' in kwargs:
            cls = kwargs.pop('cls')
        return json.dumps(c, cls=cls, **kwargs)


class _ConfigEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Config):
            return dict([(k, v) for k, v in o])
        return super(_ConfigEncoder, self).default(o)


VALID_TYPES = [Config, int, tuple, type(None), bool, float]


if _PY3:
    VALID_TYPES.extend([str,  bytes])
    string_types = str,
else:
    VALID_TYPES.extend([basestring, long, unicode])
    string_types = basestring

VALID_TYPES = tuple(VALID_TYPES)
