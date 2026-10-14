import inspect

import pytest

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


def test_flatten_function_signature_positional_only_arguments():
    # Regression test: co_posonlyargcount must be reset too, else
    # CodeType.replace() raises "bad argument to internal function".
    def f(a, b, /, c=3, **kwargs):
        return locals()

    new_f = flatten_function_signature(f)

    assert resolve_call_args(new_f, 1, 2) == f(1, 2)
    assert resolve_call_args(new_f, 1, 2, c=9, extra=True) == f(1, 2, c=9, extra=True)

    # positional-only-ness is only relevant for the *original* callable;
    # once flattened, everything is keyword-only, including former
    # positional-only arguments
    assert new_f.resolve_call_args(a=1, b=2) == f(1, 2)


def test_flatten_function_signature_no_arguments():
    def f():
        return locals()

    new_f = flatten_function_signature(f)
    assert resolve_call_args(new_f) == {}
    assert new_f() == {}


def test_resolving_decorator_preserves_metadata_and_errors():

    @resolving_decorator
    def passthrough(func, **all_kwargs):
        return func(**all_kwargs)

    @passthrough
    def myfunc(x, y=2):
        """myfunc docstring"""
        return x + y

    # metadata from the original function must be preserved
    assert myfunc.__name__ == "myfunc"
    assert myfunc.__doc__ == "myfunc docstring"
    assert str(inspect.signature(myfunc)) == "(x, y=2)"

    # normal calls still work
    assert myfunc(1) == 3
    assert myfunc(1, 5) == 6

    # calling with wrong arity still raises a normal TypeError,
    # exactly as it would for the undecorated function
    with pytest.raises(TypeError):
        myfunc(1, 2, 3)
    with pytest.raises(TypeError):
        myfunc()


def test_flatten_function_signature_keyword_only_without_varargs():
    # keyword-only arguments can exist without *args/**kwargs being used at all
    def f(a, *, b=5):
        return locals()

    new_f = flatten_function_signature(f)
    assert resolve_call_args(new_f, 1) == f(1)
    assert resolve_call_args(new_f, 1, b=9) == f(1, b=9)


def test_resolving_decorator_requires_a_caller():
    with pytest.raises(AssertionError):
        resolving_decorator(None)


def test_resolving_decorator_one_shot_call_form():
    # resolving_decorator(caller) returns a reusable decorator (partial),
    # but resolving_decorator(caller, func) can also be called directly in one shot;
    # both forms must behave identically
    def caller(func, **all_kwargs):
        return func(**all_kwargs)

    def target(x, y=2):
        return x + y

    decorated_via_partial = resolving_decorator(caller)(target)
    decorated_direct = resolving_decorator(caller, target)

    assert decorated_via_partial(1) == decorated_direct(1) == 3
    assert decorated_via_partial(1, 5) == decorated_direct(1, 5) == 6


def test_exceptions_propagate_through_resolving_decorator():

    @resolving_decorator
    def passthrough(func, **all_kwargs):
        return func(**all_kwargs)

    # exception raised by the wrapped function itself
    @passthrough
    def raiser(x):
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        raiser(1)

    # exception raised by the caller logic before/instead of calling func
    @resolving_decorator
    def caller_raiser(func, **all_kwargs):
        raise KeyError("caller failed")

    @caller_raiser
    def inner(x):
        return x

    with pytest.raises(KeyError, match="caller failed"):
        inner(1)
