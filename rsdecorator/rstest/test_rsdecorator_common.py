# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals


from rsdecorator import *



def test_common_resolving_decorator():


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

    return True
    


if __name__ == "__main__":
    assert test_common_resolving_decorator()
    print("All tests OK")