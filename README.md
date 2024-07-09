
# `easydatamodel` - The easiest way to create type-safe dataclasses in Python


Just annotate your fields and you're good to go.

```python
from easydatamodel import Model

class Person(Model):
    name: str
    age: int
```

Now you have a completely type-safe model that will validate your data for you, every time.

```python
Person(name="John Doe", age=1)  # ✅ OK
Person(name="John Doe", age="timeless")  # ❌ InvalidModelError

# easydatamodel also validates new value assignments
person = Person(name="John Doe", age=1)
person.age = "is but a number" # ❌ raises a TypeError
```
## Install

```
pip install easydatamodel
```


## Requirements
* Python 3.11+

## `easydatamodel` vs. `pydantic` and `dataclasses`

| Feature                                | `easydatamodel` | `pydantic`     | `dataclasses` |
| -------------------------------------- | --------------- | -------------- | ------------- |
| **Validates data on instantiation**    | ✅               | ✅              | ❌             |
| **Validates data on assignment**       | ✅               | Off by default | ❌             |
| **`ClassVar` validation**              | ✅               | ❌              | ❌             |
| **Automagic type coercion by default** | ❌               | ✅              | ❌             |

### Should you use `easydatamodel`?

`easydatamodel` is perfect for simple, type-safe dataclasses with minimal effort and low overhead.

However, you should consider using [`pydantic`](https://docs.pydantic.dev/) if you need more advanced features.


### `easydatamodel` as a meta-programming resource

Given the size of the `easydatamodel` codebase, **`easydatamodel` is a fantastic resource for intermediate and advanced Python developers looking to learn how Python metaprogramming works.** 

This codebase demonstrates how only a few files of Python code can create a powerful library with an ergonomic syntax.
