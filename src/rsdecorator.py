"""
An alternative to @decorator which allows you to easily fiddle with pre-resolved arguments, before transferring control to the wrapped function.

-> https://gist.github.com/pakal/dac20a15d4216b0584f0b369a78255b3
"""

import inspect
import types
import functools
from decorator import decorator
from functools import partial


def resolving_decorator(caller, func=None):
    """
    Similar to the famous decorator.decorator, except that the caller
    must be a function expecting "resolved" arguments, passed
    in a keyword-only way, and corresponding to the local variables
    in entry of the wrapped function (i.e arguments preprocessed by
    inspect.getcallargs()).

    The main effect of this preprocessing is that ``*args`` and ``**kwargs``
    arguments become simple "args" and "kwargs" variables (respectively
    expecting a tuple and a dict asvalues).

    Example::

        @resolving_decorator
        def inject_session(func, **all_kwargs):
            if not all_kwargs["session"]:
                all_kwargs["session"] = "<SESSION>"
            return func(**all_kwargs)

        @inject_session
        def myfunc(session):
            return session

        assert myfunc(None) == myfunc(session=None) == "<SESSION>"
        assert myfunc("<stuff>") == myfunc(session="<stuff>") == "<stuff>"

    """

    assert caller

    if func is None:
        return partial(resolving_decorator, caller)

    else:
        flattened_func = flatten_function_signature(func)

        def caller_wrapper(base_func, *args, **kwargs):
            assert base_func == func

            all_kwargs = flattened_func.resolve_call_args(*args, **kwargs)
            return caller(flattened_func, **all_kwargs)

        final_func = decorator(caller_wrapper, func)
        assert final_func.__name__ == func.__name__
        return final_func


def resolve_call_args(flattened_func, *args, **kwargs):
    """
    Returns an "all_args" dict containing the keywords arguments which
    which to call *flattened_func*, as if args and kwargs had been processed by the
    original, unflattened function (possibly expecting ``*args`` and ``*kwargs``
    constructs).

    This is equivalent to using inspect.getcallargs() on the original function.

    That dict can then be modified at will (eg. to insert/replace some
    arguments), before being passed to the flattened function
    that way: ``res = flattened_func(**all_args)``.
    """
    return flattened_func.resolve_call_args(*args, **kwargs)


def flatten_function_signature(func):
    """
    Takes a standard function (with possibly ``*args`` and ``*kwargs`` constructs,
    as well as keyword-only arguments with/without defaults), and
    returns a new function whose signature has these special forms
    transformed into standard, keyword-only arguments, so that the new
    function can be called simply by passing it all the keyword arguments
    that should become its initial local variables.

    Thus, a function with this signature::

       old_function(a, b, c=3, *args, **kwargs)

    becomes one with this signature::

       new_function(*, a, b, c, args, kwargs)

    This makes it possible to easily tweak/normalize all call arguments into a
    simple dict, that way::

        new_function = flatten_function_signature(func)
        all_args = resolve_call_args(new_function, *args, **kwargs)
        # here modify the dit *all_args* at will
        res = new_function(all_args)

    ..warning:
        *func* must be a user-defined function, i.e a function defined
        outside of classes, or the *im_func* attribute of a bound/unbound method.
        Do not use on bound/unbound methods directly.
    """

    old_function = func
    old_code_object = old_function.__code__

    argcount = old_code_object.co_argcount + old_code_object.co_kwonlyargcount
    flags = old_code_object.co_flags

    if flags & inspect.CO_VARARGS:
        # positional arguments were activated
        flags -= inspect.CO_VARARGS
        argcount += 1

    if flags & inspect.CO_VARKEYWORDS:
        # keyword arguments were activated
        flags -= inspect.CO_VARKEYWORDS
        argcount += 1

    # CodeType.replace() is used instead of rebuilding a CodeType from scratch,
    # since the positional layout of the CodeType constructor has kept changing
    # across python versions (eg. co_posonlyargcount, co_exceptiontable...).
    new_code_object = old_code_object.replace(
        co_argcount=0,
        co_posonlyargcount=0,
        co_kwonlyargcount=argcount,  # ALL are kwd-only arguments now
        co_flags=flags,
    )

    new_function = types.FunctionType(new_code_object,
                                      old_function.__globals__,
                                      old_function.__name__,
                                      (), # defaults from old_function.__defaults__ are useless, since they must be resolved before by inspect.getcallargs() anyway
                                      old_function.__closure__)


    new_function.original_function = old_function
    new_function.resolve_call_args = functools.partial(inspect.getcallargs, old_function)

    # we can use inspect.getfullargspec(new_function) here, to debug
    assert new_function.__name__ == old_function.__name__
    return new_function
