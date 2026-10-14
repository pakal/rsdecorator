
from rsdecorator import *


def test_py3k_resolving_decorator():

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
    
    return True


if __name__ == "__main__":
    assert test_py3k_resolving_decorator()
    print("All tests OK")