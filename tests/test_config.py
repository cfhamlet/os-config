import pytest
from os_config import Config


def test_create():
    with pytest.raises(TypeError):
        c = Config()
    c = Config.create(a=1, b=2)
    assert c.a == 1
    assert c.b == 2


def test_create_from_dict():

    d = {'a': 3, 'b': 4}
    c = Config.create_from_dict(d)

    assert c.a == 3
    assert c.b == 4


def test_simple_recursion():
    c = Config.create()
    with pytest.raises(AttributeError):
        c.c = c


def test_tuple_recursion():

    c = Config.create()
    with pytest.raises(AttributeError):
        c.c = (c, )


def test_deep_recursion():
    a = Config.create()
    b = Config.create()
    c = Config.create()

    b.c = c
    c.a = a
    with pytest.raises(AttributeError):
        a.b = b


def test_invalid_attribute_name():
    c = Config.create()
    for k in ['1', '_a', '*']:
        with pytest.raises(AttributeError):
            setattr(c, k, None)

def test_valid_type():
    c = Config.create()
    for v in [1, False, (1, 2), None, 1.1, Config.create()]:
        setattr(c, 'test_key', v)
        assert getattr(c, 'test_key') == v
    


def test_invalid_type():
    class TestClass(object):
        pass

    def test_method():
        pass

    c = Config.create()
    for v in [{}, [1, 2], TestClass, TestClass(), test_method, ]:
        with pytest.raises(AttributeError):
            c.c = v


def test_update_from_config_01():
    c = Config.create(a=1, b=2)
    d = Config.create()
    d.update(c)
    assert d.a == 1
    assert d.b == 2


def test_update_from_config_02():
    c = Config.create(a=1, b=2)
    d = Config.create()

    d.a = 2
    d.update(c)
    assert d.a == 1


def test_udpate_from_config_recursive_01():
    c = Config.create()
    d = Config.create()
    d.m = c
    with pytest.raises(AttributeError):
        c.update(d)


def test_udpate_from_config_recursive_02():
    c = Config.create()
    d = Config.create()
    d.m = (c,)
    with pytest.raises(AttributeError):
        c.update(d)


def test_udpate_from_config_recursive_03():
    c = Config.create()
    d = Config.create()
    e = Config.create()
    e.m = c
    d.m = (e,)
    with pytest.raises(AttributeError):
        c.update(d)


def test_update_from_dict_01():
    c = Config.create()
    c.update({'a': 1, 'b': 2})
    assert c.a == 1
    assert c.b == 2


def test_update_from_dict_02():
    c = Config.create()
    d = {'a': {'b': 1}}
    c.update(d)
    assert c.a.b == 1


def test_update_from_dict_03():
    c = Config.create()
    b = Config.create(b=1)
    d = {'a': b}
    c.update(d)
    assert c.a.b == 1


def test_update_from_dict_04():
    c = Config.create(a=1)
    assert c.a == 1
    b = Config.create(b=1)
    d = {'a': b}
    c.update(d)
    assert c.a.b == 1


def test_update_from_dict_05():
    c = Config.create()
    b = Config.create(b=1)
    d = {'a': b}
    c.update(d)
    d = {'a': 1}
    c.update(d)
    assert c.a == 1


def test_create_from_json_01():
    d = {'a': 1}
    import json
    j = json.dumps(d)
    c = Config.create_from_json(j)
    assert c.a == 1


def test_dump_to_json_01():
    c = Config.create(a=1)
    j = Config.to_json(c)
    import json
    d = json.loads(j)
    assert d['a'] == 1
