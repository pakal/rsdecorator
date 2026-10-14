from rsdecorator import *


def test_resolving_decorator():

    def f(a, b=3, c=8, *d, **e):
        return locals()
    new_f = flatten_function_signature(f)

    assert resolve_call_args(new_f, 1, 2) == new_f.resolve_call_args(1, 2)
    assert resolve_call_args(new_f, a=66, k=True) == new_f.resolve_call_args(a=66, k=True)

    assert resolve_call_args(new_f, 1, 2) == {'b': 2, 'c': 8, 'a': 1, 'd': (), 'e': {}}
    assert resolve_call_args(new_f, a=66, k=True) == {'b': 3, 'c': 8, 'a': 66, 'd': (), 'e': {'k': True}}



    @resolving_decorator
    def inject_session(func, **all_kwargs):
        if not all_kwargs["session"]:
            all_kwargs["session"] = "<SESSION>"
        return func(**all_kwargs)

    @inject_session
    def func1(session):
        return session

    @inject_session
    def func2(a, session=None):
        return session

    @inject_session
    def func3(a, *session):
        return session

    @inject_session
    def func4(a, **session):
        return session

    assert func1(None) == "<SESSION>"
    assert func1(4) == 4
    assert func2(1, None) == "<SESSION>"
    assert func2(1, 5) == 5
    assert func3(1) == "<SESSION>"
    assert func3(1, 8) == (8,)
    assert func4(1) == "<SESSION>"
    assert func4(1, my=8) == dict(my=8)


def test_resolving_decorator_advanced_signature():

    # we only take the most complex case possible, here
    def gen(aa, bb):
        def _my_advanced(a, b, c, *d, kw1, kwother=66, **e):
            cc = (aa, bb)
            return locals()
        return _my_advanced
    advanced = gen(1, 2)

    new_advanced = flatten_function_signature(advanced)
    assert new_advanced.original_function == advanced
    res1 = advanced(1, 2, 3, 4, 5, kw1="a", kw2="b")

    try:
        new_advanced(1, 2, 3, (4, 5), "a", 66, dict(kw2="b"))
        assert False
    except TypeError as e:
        assert "takes 0 positional arguments" in str(e)

    try:
        new_advanced(**dict(a=1, b=2, c=3, d=(4,5), kw1="a", e=dict(kw2="b")))
        assert False
    except TypeError as e:
        assert "missing 1 required keyword-only argument" in str(e) # default values are well LOST (for kwother here)

    res2 = new_advanced(**dict(a=1, b=2, c=3, d=(4,5), kw1="a", kwother=66, e=dict(kw2="b")))

    assert res1 == res2, (res1, res2)
