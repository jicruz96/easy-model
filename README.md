
# `easy-model` - The easiest way to create type-safe dataclasses in Python


Just annotate your fields and you're good to go.

```python
from easy_model import Model

class Person(Model):
    name: str
    age: int
```

Now you have a completely type-safe model that will validate your data for you, every time.

```python
Person(name="John Doe", age=1)  # ✅ OK
Person(name="John Doe", age="timeless")  # ❌ InvalidModelError

# easy-model also validates new value assignments
person = Person(name="John Doe", age=1)
person.age = "is but a number" # ❌ raises a TypeError
```
## Install

```
pip install easy-model
```


## Requirements
* Python 3.10+

## `easy-model` vs. `pydantic` and `dataclasses`

| Feature                             | `easy-model` | `pydantic`     | `dataclasses` |
| ----------------------------------- | ------------ | -------------- | ------------- |
| **Validates data on instantiation** | ✅            | ✅              | ❌             |
| **Validates data on assignment**    | ✅            | Off by default | ❌             |
| **`ClassVar` validation**           | ✅            | ❌              | ❌             |

### Should you use `easy-model`?

`easy-model` is perfect for simple, type-safe dataclasses with minimal effort and low overhead.

However, you should consider using [`pydantic`](https://docs.pydantic.dev/) if you need more advanced features.


### `easy-model` as a meta-programming resource

Given the size of the `easy-model` codebase, **`easy-model` is a fantastic resource for intermediate and advanced Python developers looking to learn how Python metaprogramming works.** 

This codebase demonstrates how only a few files of Python code can create a powerful library with an ergonomic syntax.
