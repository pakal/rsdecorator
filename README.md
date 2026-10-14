# RSDecorator

An alternative to `@decorator` which allows you to easily fiddle with pre-resolved arguments, before transferring control to the wrapped function.

See the project repository: https://github.com/pakal/rsdecorator

Originally published as a gist: https://gist.github.com/pakal/dac20a15d4216b0584f0b369a78255b3

## Installation

```bash
pip install RSDecorator
```

## Example

```python
from rsdecorator import resolving_decorator

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
```

## Development

```bash
pip install -e .[test]
pytest
```

Run the full test matrix across supported Python versions with:

```bash
tox
```
