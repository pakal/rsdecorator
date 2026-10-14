# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals


from rsdecorator import *


def test_py2k_resolving_decorator():

    # testing with normal functions and nested functions #
    
    tested_funcs = []
    
    def f(a, b=3, c=8, *d, **e):
        return locals()
    tested_funcs.append(f)
    
    def gen(aa, bb):
        def f(a, b=3, c=8, *d, **e):
            cc = (aa, bb)
            return locals()
        return f
    tested_funcs.append(gen(1, 2))
    
    for old_function in tested_funcs:
        new_function = flatten_function_signature(old_function)
        assert new_function.original_function == old_function
        
        res1 = old_function(1, 2, 3, 4, 5, kw1="a", kw2="b")
        res2 = new_function(1, 2, 3, (4, 5), dict(kw1="a", kw2="b"))
        res3 = new_function(**dict(a=1, b=2, c=3, d=(4, 5), e=dict(dict(kw1="a", kw2="b"))))
        
        assert res1 == res2, (res1, res2)
        assert res1 == res3, (res1, res3)

    return True
    


if __name__ == "__main__":
    assert test_py2k_resolving_decorator()
    print("All tests OK")