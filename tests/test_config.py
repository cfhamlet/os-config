import pytest
from os_config import Config
from os_config.config import allowed_upper


def test_create():
    with pytest.raises(TypeError):
        c = Config()
    c = Config.create(a=1, b=2)
    assert c.a == 1
    assert c.b == 2


def test_create_from_dict():

    d = {'a': 3, 'b': 4}
    c = Config.from_dict(d)

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
    for v in [TestClass, TestClass(), test_method, ]:
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
    c = Config.from_json(j)
    assert c.a == 1


def test_dump_to_json_01():
    c = Config.create(a=1)
    j = Config.to_json(c)
    import json
    d = json.loads(j)
    assert d['a'] == 1


def test_key_filter_01():
    c = Config.create(a=1, key_filter=allowed_upper)
    assert not hasattr(c, 'a')

    c.b = 1
    assert not hasattr(c, 'b')

    c.C = 1
    assert hasattr(c, 'C')


def test_tuple_with_list():
    d = {'a': (1, 2, [1, 2, 3])}
    c = Config.from_dict(d)
    assert c.a == (1, 2, (1, 2, 3))


def test_tuple_with_dict():
    d = {'a': (1, {'b': 2}, [3, 4, 5])}

    c = Config.from_dict(d)
    assert c.a[1].b == 2


def test_create_from_object():
    class A(object):
        a = 1
    c = Config.from_object(A)
    assert c.a == 1


def test_sub_config():
    c = Config.create()
    a = Config.create()
    c.a = a
    c.b = a
    c.a = 1
    with pytest.raises(AttributeError):
        a.c = c


def test_sub_config_with_key_filter():
    c = Config.create(key_filter=lambda x: x.isupper())
    d = Config.create(a=1, B=2)
    c.M = d
    assert c.M.a == 1
    assert c.M.B == 2

    c.update({'N': {'o': 1}, 'P': {'O': 2}})
    assert not hasattr(c.N, 'o')
    assert c.P.O == 2


def test_assign_list():
    c = Config.create(a=[1, 2, 3])
    assert c.a == (1, 2, 3)
    c.b = [3, 4, 5]
    assert c.b == (3, 4, 5)


def test_set_dict():
    c = Config.create()
    c.a = {"b": 1}
    assert c.a.b == 1


def test_set_config():
    c = Config.create(key_filter=lambda x: x.isupper())

    b = Config.create()
    b.m = 1
    c.B = b
    assert c.B.m == 1
    c.C = {'a': 1}
    assert not hasattr(c.C, 'a')


def test_from_pyfile(tmpdir):
    txt = r'''
a = 1
b = [1,2,3]
'''
    f = tmpdir.join('test_config.py')
    f.write(txt)
    c = Config.from_pyfile(f.strpath)
    assert c.a == 1
    assert c.b == (1, 2, 3)


def test_get():
    c = Config.create(a=1)
    assert c.get('a') == 1
    assert c.get('b') is None
    assert c.get('c', 2) == 2
