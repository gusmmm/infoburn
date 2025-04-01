- API documentation at https://docs.pydantic.dev/latest/api/base_model/

---
title: "Models - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/models/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
API Documentation

[`pydantic.main.BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel)  

One of the primary ways of defining schema in Pydantic is via models. Models are simply classes which inherit from [`BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel) and define fields as annotated attributes.

You can think of models as similar to structs in languages like C, or as the requirements of a single endpoint in an API.

Models share many similarities with Python's [dataclasses](https://docs.python.org/3/library/dataclasses.html#module-dataclasses), but have been designed with some subtle-yet-important differences that streamline certain workflows related to validation, serialization, and JSON schema generation. You can find more discussion of this in the [Dataclasses](https://docs.pydantic.dev/latest/concepts/dataclasses/) section of the docs.

Untrusted data can be passed to a model and, after parsing and validation, Pydantic guarantees that the fields of the resultant model instance will conform to the field types defined on the model.

Validation — a *deliberate* misnomer

### TL;DR

We use the term "validation" to refer to the process of instantiating a model (or other type) that adheres to specified types and constraints. This task, which Pydantic is well known for, is most widely recognized as "validation" in colloquial terms, even though in other contexts the term "validation" may be more restrictive.

---

### The long version

The potential confusion around the term "validation" arises from the fact that, strictly speaking, Pydantic's primary focus doesn't align precisely with the dictionary definition of "validation":

> ### validation
> 
> *noun* the action of checking or proving the validity or accuracy of something.

In Pydantic, the term "validation" refers to the process of instantiating a model (or other type) that adheres to specified types and constraints. Pydantic guarantees the types and constraints of the output, not the input data. This distinction becomes apparent when considering that Pydantic's `ValidationError` is raised when data cannot be successfully parsed into a model instance.

While this distinction may initially seem subtle, it holds practical significance. In some cases, "validation" goes beyond just model creation, and can include the copying and coercion of data. This can involve copying arguments passed to the constructor in order to perform coercion to a new type without mutating the original input data. For a more in-depth understanding of the implications for your usage, refer to the [Data Conversion](https://docs.pydantic.dev/latest/concepts/models/#data-conversion) and [Attribute Copies](https://docs.pydantic.dev/latest/concepts/models/#attribute-copies) sections below.

In essence, Pydantic's primary goal is to assure that the resulting structure post-processing (termed "validation") precisely conforms to the applied type hints. Given the widespread adoption of "validation" as the colloquial term for this process, we will consistently use it in our documentation.

While the terms "parse" and "validation" were previously used interchangeably, moving forward, we aim to exclusively employ "validate", with "parse" reserved specifically for discussions related to [JSON parsing](https://docs.pydantic.dev/latest/concepts/json/).

## Basic model usage¶

Note

Pydantic relies heavily on the existing Python typing constructs to define models. If you are not familiar with those, the following resources can be useful:

- The [Type System Guides](https://typing.readthedocs.io/en/latest/guides/index.html)
- The [mypy documentation](https://mypy.readthedocs.io/en/latest/)

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    id: int
    name: str = 'Jane Doe'

    model_config = ConfigDict(str_max_length=10)  
```

In this example, `User` is a model with two fields:

- `id`, which is an integer and is required
- `name`, which is a string and is not required (it has a default value).

Fields can be customized in a number of ways using the [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) function. See the [documentation on fields](https://docs.pydantic.dev/latest/concepts/fields/) for more information.

The model can then be instantiated:

`user` is an instance of `User`. Initialization of the object will perform all parsing and validation. If no [`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) exception is raised, you know the resulting model instance is valid.

Fields of a model can be accessed as normal attributes of the `user` object:

```python
assert user.name == 'Jane Doe'  
assert user.id == 123  
assert isinstance(user.id, int)
```

The model instance can be serialized using the [`model_dump()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump) method:

```python
assert user.model_dump() == {'id': 123, 'name': 'Jane Doe'}
```

Calling [dict](https://docs.python.org/3/reference/expressions.html#dict) on the instance will also provide a dictionary, but nested fields will not be recursively converted into dictionaries. [`model_dump()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump) also provides numerous arguments to customize the serialization result.

By default, models are mutable and field values can be changed through attribute assignment:

```python
user.id = 321
assert user.id == 321
```

Warning

When defining your models, watch out for naming collisions between your field name and its type annotation.

For example, the following will not behave as expected and would yield a validation error:

```python
from typing import Optional

from pydantic import BaseModel

class Boo(BaseModel):
    int: Optional[int] = None

m = Boo(int=123)  # Will fail to validate.
```

Because of how Python evaluates [annotated assignment statements](https://docs.python.org/3/reference/simple_stmts.html#annassign), the statement is equivalent to `int: None = None`, thus leading to a validation error.

### Model methods and properties¶

The example above only shows the tip of the iceberg of what models can do. Models possess the following methods and attributes:

- [`model_validate()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate): Validates the given object against the Pydantic model. See [Validating data](https://docs.pydantic.dev/latest/concepts/models/#validating-data).
- [`model_validate_json()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_json): Validates the given JSON data against the Pydantic model. See [Validating data](https://docs.pydantic.dev/latest/concepts/models/#validating-data).
- [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct): Creates models without running validation. See [Creating models without validation](https://docs.pydantic.dev/latest/concepts/models/#creating-models-without-validation).
- [`model_dump()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump): Returns a dictionary of the model's fields and values. See [Serialization](https://docs.pydantic.dev/latest/concepts/serialization/#model_dump).
- [`model_dump_json()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json): Returns a JSON string representation of [`model_dump()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump). See [Serialization](https://docs.pydantic.dev/latest/concepts/serialization/#model_dump_json).
- [`model_copy()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_copy): Returns a copy (by default, shallow copy) of the model. See [Serialization](https://docs.pydantic.dev/latest/concepts/serialization/#model_copy).
- [`model_json_schema()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_json_schema): Returns a jsonable dictionary representing the model's JSON Schema. See [JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/).
- [`model_fields`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_fields): A mapping between field names and their definitions ([`FieldInfo`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.FieldInfo) instances).
- [`model_computed_fields`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_computed_fields): A mapping between computed field names and their definitions ([`ComputedFieldInfo`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.ComputedFieldInfo) instances).
- [`model_extra`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_extra): The extra fields set during validation.
- [`model_fields_set`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_fields_set): The set of fields which were explicitly provided when the model was initialized.
- [`model_parametrized_name()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_parametrized_name): Computes the class name for parametrizations of generic classes.
- [`model_post_init()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_post_init): Performs additional actions after the model is instantiated and all field validators are applied.
- [`model_rebuild()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_rebuild): Rebuilds the model schema, which also supports building recursive generic models. See [Rebuilding model schema](https://docs.pydantic.dev/latest/concepts/models/#rebuilding-model-schema).

Note

See the API documentation of [`BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel) for the class definition including a full list of methods and attributes.

## Data conversion¶

Pydantic may cast input data to force it to conform to model field types, and in some cases this may result in a loss of information. For example:

```python
from pydantic import BaseModel

class Model(BaseModel):
    a: int
    b: float
    c: str

print(Model(a=3.000, b='2.72', c=b'binary data').model_dump())
#> {'a': 3, 'b': 2.72, 'c': 'binary data'}
```

This is a deliberate decision of Pydantic, and is frequently the most useful approach. See [here](https://github.com/pydantic/pydantic/issues/578) for a longer discussion on the subject.

Nevertheless, Pydantic provides a [strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/), where no data conversion is performed. Values must be of the same type than the declared field type.

This is also the case for collections. In most cases, you shouldn't make use of abstract container classes and just use a concrete type, such as [`list`](https://docs.python.org/3/glossary.html#term-list):

```python
from pydantic import BaseModel

class Model(BaseModel):
    items: list[int]  

print(Model(items=(1, 2, 3)))
#> items=[1, 2, 3]
```

Besides, using these abstract types can also lead to [poor validation performance](https://docs.pydantic.dev/latest/concepts/performance/#sequence-vs-list-or-tuple-with-mapping-vs-dict), and in general using concrete container types will avoid unnecessary checks.

By default, Pydantic models **won't error when you provide extra data**, and these values will simply be ignored:

```python
from pydantic import BaseModel

class Model(BaseModel):
    x: int

m = Model(x=1, y='a')
assert m.model_dump() == {'x': 1}
```

The [`extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) configuration value can be used to control this behavior:

```python
from pydantic import BaseModel, ConfigDict

class Model(BaseModel):
    x: int

    model_config = ConfigDict(extra='allow')

m = Model(x=1, y='a')  
assert m.model_dump() == {'x': 1, 'y': 'a'}
assert m.__pydantic_extra__ == {'y': 'a'}
```

The configuration can take three values:

- `'ignore'`: Providing extra data is ignored (the default).
- `'forbid'`: Providing extra data is not permitted.
- `'allow'`: Providing extra data is allowed and stored in the `__pydantic_extra__` dictionary attribute. The `__pydantic_extra__` can explicitly be annotated to provide validation for extra fields.

For more details, refer to the [`extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) API documentation.

Pydantic dataclasses also support extra data (see the [dataclass configuration](https://docs.pydantic.dev/latest/concepts/dataclasses/#dataclass-config) section).

## Nested models¶

More complex hierarchical data structures can be defined using models themselves as types in annotations.

```
from typing import Optional

from pydantic import BaseModel

class Foo(BaseModel):
    count: int
    size: Optional[float] = None

class Bar(BaseModel):
    apple: str = 'x'
    banana: str = 'y'

class Spam(BaseModel):
    foo: Foo
    bars: list[Bar]

m = Spam(foo={'count': 4}, bars=[{'apple': 'x1'}, {'apple': 'x2'}])
print(m)
"""
foo=Foo(count=4, size=None) bars=[Bar(apple='x1', banana='y'), Bar(apple='x2', banana='y')]
"""
print(m.model_dump())
"""
{
    'foo': {'count': 4, 'size': None},
    'bars': [{'apple': 'x1', 'banana': 'y'}, {'apple': 'x2', 'banana': 'y'}],
}
"""
```

```
from pydantic import BaseModel

class Foo(BaseModel):
    count: int
    size: float | None = None

class Bar(BaseModel):
    apple: str = 'x'
    banana: str = 'y'

class Spam(BaseModel):
    foo: Foo
    bars: list[Bar]

m = Spam(foo={'count': 4}, bars=[{'apple': 'x1'}, {'apple': 'x2'}])
print(m)
"""
foo=Foo(count=4, size=None) bars=[Bar(apple='x1', banana='y'), Bar(apple='x2', banana='y')]
"""
print(m.model_dump())
"""
{
    'foo': {'count': 4, 'size': None},
    'bars': [{'apple': 'x1', 'banana': 'y'}, {'apple': 'x2', 'banana': 'y'}],
}
"""
```

Self-referencing models are supported. For more details, see the documentation related to [forward annotations](https://docs.pydantic.dev/latest/concepts/forward_annotations/#self-referencing-or-recursive-models).

## Rebuilding model schema¶

When you define a model class in your code, Pydantic will analyze the body of the class to collect a variety of information required to perform validation and serialization, gathered in a core schema. Notably, the model's type annotations are evaluated to understand the valid types for each field (more information can be found in the [Architecture](https://docs.pydantic.dev/latest/internals/architecture/) documentation). However, it might be the case that annotations refer to symbols not defined when the model class is being created. To circumvent this issue, the [`model_rebuild()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_rebuild) method can be used:

```python
from pydantic import BaseModel, PydanticUserError

class Foo(BaseModel):
    x: 'Bar'  

try:
    Foo.model_json_schema()
except PydanticUserError as e:
    print(e)
    """
    \`Foo\` is not fully defined; you should define \`Bar\`, then call \`Foo.model_rebuild()\`.

    For further information visit https://errors.pydantic.dev/2/u/class-not-fully-defined
    """

class Bar(BaseModel):
    pass

Foo.model_rebuild()
print(Foo.model_json_schema())
"""
{
    '$defs': {'Bar': {'properties': {}, 'title': 'Bar', 'type': 'object'}},
    'properties': {'x': {'$ref': '#/$defs/Bar'}},
    'required': ['x'],
    'title': 'Foo',
    'type': 'object',
}
"""
```

Pydantic tries to determine when this is necessary automatically and error if it wasn't done, but you may want to call [`model_rebuild()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_rebuild) proactively when dealing with recursive models or generics.

In V2, [`model_rebuild()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_rebuild) replaced `update_forward_refs()` from V1. There are some slight differences with the new behavior. The biggest change is that when calling [`model_rebuild()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_rebuild) on the outermost model, it builds a core schema used for validation of the whole model (nested models and all), so all types at all levels need to be ready before [`model_rebuild()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_rebuild) is called.

## Arbitrary class instances¶

(Formerly known as "ORM Mode"/`from_orm`).

Pydantic models can also be created from arbitrary class instances by reading the instance attributes corresponding to the model field names. One common application of this functionality is integration with object-relational mappings (ORMs).

To do this, set the [`from_attributes`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.from_attributes) config value to `True` (see the documentation on [Configuration](https://docs.pydantic.dev/latest/concepts/config/) for more details).

The example here uses [SQLAlchemy](https://www.sqlalchemy.org/), but the same approach should work for any ORM.

```python
from typing import Annotated

from sqlalchemy import ARRAY, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pydantic import BaseModel, ConfigDict, StringConstraints

class Base(DeclarativeBase):
    pass

class CompanyOrm(Base):
    __tablename__ = 'companies'

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    public_key: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False, unique=True
    )
    domains: Mapped[list[str]] = mapped_column(ARRAY(String(255)))

class CompanyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_key: Annotated[str, StringConstraints(max_length=20)]
    domains: list[Annotated[str, StringConstraints(max_length=255)]]

co_orm = CompanyOrm(
    id=123,
    public_key='foobar',
    domains=['example.com', 'foobar.com'],
)
print(co_orm)
#> <__main__.CompanyOrm object at 0x0123456789ab>
co_model = CompanyModel.model_validate(co_orm)
print(co_model)
#> id=123 public_key='foobar' domains=['example.com', 'foobar.com']
```

### Nested attributes¶

When using attributes to parse models, model instances will be created from both top-level attributes and deeper-nested attributes as appropriate.

Here is an example demonstrating the principle:

```python
from pydantic import BaseModel, ConfigDict

class PetCls:
    def __init__(self, *, name: str, species: str):
        self.name = name
        self.species = species

class PersonCls:
    def __init__(self, *, name: str, age: float = None, pets: list[PetCls]):
        self.name = name
        self.age = age
        self.pets = pets

class Pet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    species: str

class Person(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    age: float = None
    pets: list[Pet]

bones = PetCls(name='Bones', species='dog')
orion = PetCls(name='Orion', species='cat')
anna = PersonCls(name='Anna', age=20, pets=[bones, orion])
anna_model = Person.model_validate(anna)
print(anna_model)
"""
name='Anna' age=20.0 pets=[Pet(name='Bones', species='dog'), Pet(name='Orion', species='cat')]
"""
```

## Error handling¶

Pydantic will raise a [`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) exception whenever it finds an error in the data it's validating.

A single exception will be raised regardless of the number of errors found, and that validation error will contain information about all of the errors and how they happened.

See [Error Handling](https://docs.pydantic.dev/latest/errors/errors/) for details on standard and custom errors.

As a demonstration:

```python
from pydantic import BaseModel, ValidationError

class Model(BaseModel):
    list_of_ints: list[int]
    a_float: float

data = dict(
    list_of_ints=['1', 2, 'bad'],
    a_float='not a float',
)

try:
    Model(**data)
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    list_of_ints.2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='bad', input_type=str]
    a_float
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='not a float', input_type=str]
    """
```

## Validating data¶

Pydantic provides three methods on models classes for parsing data:

- [`model_validate()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate): this is very similar to the `__init__` method of the model, except it takes a dictionary or an object rather than keyword arguments. If the object passed cannot be validated, or if it's not a dictionary or instance of the model in question, a [`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) will be raised.
- [`model_validate_json()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_json): this validates the provided data as a JSON string or `bytes` object. If your incoming data is a JSON payload, this is generally considered faster (instead of manually parsing the data as a dictionary). Learn more about JSON parsing in the [JSON](https://docs.pydantic.dev/latest/concepts/json/) section of the docs.
- [`model_validate_strings()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_strings): this takes a dictionary (can be nested) with string keys and values and validates the data in JSON mode so that said strings can be coerced into the correct types.

```
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None

m = User.model_validate({'id': 123, 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

try:
    User.model_validate(['not', 'a', 'dict'])
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Input should be a valid dictionary or instance of User [type=model_type, input_value=['not', 'a', 'dict'], input_type=list]
    """

m = User.model_validate_json('{"id": 123, "name": "James"}')
print(m)
#> id=123 name='James' signup_ts=None

try:
    m = User.model_validate_json('{"id": 123, "name": 123}')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Input should be a valid string [type=string_type, input_value=123, input_type=int]
    """

try:
    m = User.model_validate_json('invalid JSON')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='invalid JSON', input_type=str]
    """

m = User.model_validate_strings({'id': '123', 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

m = User.model_validate_strings(
    {'id': '123', 'name': 'James', 'signup_ts': '2024-04-01T12:00:00'}
)
print(m)
#> id=123 name='James' signup_ts=datetime.datetime(2024, 4, 1, 12, 0)

try:
    m = User.model_validate_strings(
        {'id': '123', 'name': 'James', 'signup_ts': '2024-04-01'}, strict=True
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    signup_ts
      Input should be a valid datetime, invalid datetime separator, expected \`T\`, \`t\`, \`_\` or space [type=datetime_parsing, input_value='2024-04-01', input_type=str]
    """
```

```
from datetime import datetime

from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: datetime | None = None

m = User.model_validate({'id': 123, 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

try:
    User.model_validate(['not', 'a', 'dict'])
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Input should be a valid dictionary or instance of User [type=model_type, input_value=['not', 'a', 'dict'], input_type=list]
    """

m = User.model_validate_json('{"id": 123, "name": "James"}')
print(m)
#> id=123 name='James' signup_ts=None

try:
    m = User.model_validate_json('{"id": 123, "name": 123}')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Input should be a valid string [type=string_type, input_value=123, input_type=int]
    """

try:
    m = User.model_validate_json('invalid JSON')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
      Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='invalid JSON', input_type=str]
    """

m = User.model_validate_strings({'id': '123', 'name': 'James'})
print(m)
#> id=123 name='James' signup_ts=None

m = User.model_validate_strings(
    {'id': '123', 'name': 'James', 'signup_ts': '2024-04-01T12:00:00'}
)
print(m)
#> id=123 name='James' signup_ts=datetime.datetime(2024, 4, 1, 12, 0)

try:
    m = User.model_validate_strings(
        {'id': '123', 'name': 'James', 'signup_ts': '2024-04-01'}, strict=True
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    signup_ts
      Input should be a valid datetime, invalid datetime separator, expected \`T\`, \`t\`, \`_\` or space [type=datetime_parsing, input_value='2024-04-01', input_type=str]
    """
```

If you want to validate serialized data in a format other than JSON, you should load the data into a dictionary yourself and then pass it to [`model_validate`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate).

Note

Depending on the types and model configs involved, [`model_validate`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate) and [`model_validate_json`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_json) may have different validation behavior. If you have data coming from a non-JSON source, but want the same validation behavior and errors you'd get from [`model_validate_json`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_json), our recommendation for now is to use either use `model_validate_json(json.dumps(data))`, or use [`model_validate_strings`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_strings) if the data takes the form of a (potentially nested) dictionary with string keys and values.

Note

If you're passing in an instance of a model to [`model_validate`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate), you will want to consider setting [`revalidate_instances`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.revalidate_instances) in the model's config. If you don't set this value, then validation will be skipped on model instances. See the below example:

```
from pydantic import BaseModel

class Model(BaseModel):
    a: int

m = Model(a=0)
# note: setting \`validate_assignment\` to \`True\` in the config can prevent this kind of misbehavior.
m.a = 'not an int'

# doesn't raise a validation error even though m is invalid
m2 = Model.model_validate(m)
```

```
from pydantic import BaseModel, ConfigDict, ValidationError

class Model(BaseModel):
    a: int

    model_config = ConfigDict(revalidate_instances='always')

m = Model(a=0)
# note: setting \`validate_assignment\` to \`True\` in the config can prevent this kind of misbehavior.
m.a = 'not an int'

try:
    m2 = Model.model_validate(m)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    a
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not an int', input_type=str]
    """
```

### Creating models without validation¶

Pydantic also provides the [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct) method, which allows models to be created **without validation**. This can be useful in at least a few cases:

- when working with complex data that is already known to be valid (for performance reasons)
- when one or more of the validator functions are non-idempotent
- when one or more of the validator functions have side effects that you don't want to be triggered.

Warning

[`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct) does not do any validation, meaning it can create models which are invalid. **You should only ever use the [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct) method with data which has already been validated, or that you definitely trust.**

Note

In Pydantic V2, the performance gap between validation (either with direct instantiation or the `model_validate*` methods) and [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct) has been narrowed considerably. For simple models, going with validation may even be faster. If you are using [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct) for performance reasons, you may want to profile your use case before assuming it is actually faster.

Note that for [root models](https://docs.pydantic.dev/latest/concepts/models/#rootmodel-and-custom-root-types), the root value can be passed to [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct) positionally, instead of using a keyword argument.

Here are some additional notes on the behavior of [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct):

- When we say "no validation is performed" — this includes converting dictionaries to model instances. So if you have a field referring to a model type, you will need to convert the inner dictionary to a model yourself.
- If you do not pass keyword arguments for fields with defaults, the default values will still be used.
- For models with private attributes, the `__pydantic_private__` dictionary will be populated the same as it would be when creating the model with validation.
- No `__init__` method from the model or any of its parent classes will be called, even when a custom `__init__` method is defined.

On [extra data](https://docs.pydantic.dev/latest/concepts/models/#extra-data) behavior with [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct)

- For models with [`extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) set to `'allow'`, data not corresponding to fields will be correctly stored in the `__pydantic_extra__` dictionary and saved to the model's `__dict__` attribute.
- For models with [`extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) set to `'ignore'`, data not corresponding to fields will be ignored — that is, not stored in `__pydantic_extra__` or `__dict__` on the instance.
- Unlike when instiating the model with validation, a call to [`model_construct()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_construct) with [`extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) set to `'forbid'` doesn't raise an error in the presence of data not corresponding to fields. Rather, said input data is simply ignored.

## Generic models¶

Pydantic supports the creation of generic models to make it easier to reuse a common model structure. Both the new [type parameter syntax](https://docs.python.org/3/reference/compound_stmts.html#type-params) (introduced by [PEP 695](https://peps.python.org/pep-0695/) in Python 3.12) and the old syntax are supported (refer to [the Python documentation](https://docs.python.org/3/library/typing.html#building-generic-types-and-type-aliases) for more details).

Here is an example using a generic Pydantic model to create an easily-reused HTTP response payload wrapper:

```
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

DataT = TypeVar('DataT')  

class DataModel(BaseModel):
    number: int

class Response(BaseModel, Generic[DataT]):  
    data: DataT  

print(Response[int](data=1))
#> data=1
print(Response[str](data='value'))
#> data='value'
print(Response[str](data='value').model_dump())
#> {'data': 'value'}

data = DataModel(number=1)
print(Response[DataModel](data=data).model_dump())
#> {'data': {'number': 1}}
try:
    Response[int](data='value')
except ValidationError as e:
    print(e)
    """
    1 validation error for Response[int]
    data
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='value', input_type=str]
    """
```

```python
from pydantic import BaseModel, ValidationError

class DataModel(BaseModel):
    number: int

class Response[DataT](BaseModel):  
    data: DataT  

print(Response[int](data=1))
#> data=1
print(Response[str](data='value'))
#> data='value'
print(Response[str](data='value').model_dump())
#> {'data': 'value'}

data = DataModel(number=1)
print(Response[DataModel](data=data).model_dump())
#> {'data': {'number': 1}}
try:
    Response[int](data='value')
except ValidationError as e:
    print(e)
    """
    1 validation error for Response[int]
    data
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='value', input_type=str]
    """
```

1. Declare a Pydantic model and add the list of type variables as type parameters.
2. Use the type variables as annotations where you will want to replace them with other types.

Warning

When parametrizing a model with a concrete type, Pydantic **does not** validate that the provided type is [assignable to the type variable](https://typing.readthedocs.io/en/latest/spec/generics.html#type-variables-with-an-upper-bound) if it has an upper bound.

Any [configuration](https://docs.pydantic.dev/latest/concepts/config/), [validation](https://docs.pydantic.dev/latest/concepts/validators/) or [serialization](https://docs.pydantic.dev/latest/concepts/serialization/) logic set on the generic model will also be applied to the parametrized classes, in the same way as when inheriting from a model class. Any custom methods or attributes will also be inherited.

Generic models also integrate properly with type checkers, so you get all the type checking you would expect if you were to declare a distinct type for each parametrization.

Note

Internally, Pydantic creates subclasses of the generic model at runtime when the generic model class is parametrized. These classes are cached, so there should be minimal overhead introduced by the use of generics models.

To inherit from a generic model and preserve the fact that it is generic, the subclass must also inherit from [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic):

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

TypeX = TypeVar('TypeX')

class BaseClass(BaseModel, Generic[TypeX]):
    X: TypeX

class ChildClass(BaseClass[TypeX], Generic[TypeX]):
    pass

# Parametrize \`TypeX\` with \`int\`:
print(ChildClass[int](X=1))
#> X=1
```

You can also create a generic subclass of a model that partially or fully replaces the type variables in the superclass:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

TypeX = TypeVar('TypeX')
TypeY = TypeVar('TypeY')
TypeZ = TypeVar('TypeZ')

class BaseClass(BaseModel, Generic[TypeX, TypeY]):
    x: TypeX
    y: TypeY

class ChildClass(BaseClass[int, TypeY], Generic[TypeY, TypeZ]):
    z: TypeZ

# Parametrize \`TypeY\` with \`str\`:
print(ChildClass[str, int](x='1', y='y', z='3'))
#> x=1 y='y' z=3
```

If the name of the concrete subclasses is important, you can also override the default name generation by overriding the [`model_parametrized_name()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_parametrized_name) method:

```python
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar('DataT')

class Response(BaseModel, Generic[DataT]):
    data: DataT

    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        return f'{params[0].__name__.title()}Response'

print(repr(Response[int](data=1)))
#> IntResponse(data=1)
print(repr(Response[str](data='a')))
#> StrResponse(data='a')
```

You can use parametrized generic models as types in other models:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    content: T

class Product(BaseModel):
    name: str
    price: float

class Order(BaseModel):
    id: int
    product: ResponseModel[Product]

product = Product(name='Apple', price=0.5)
response = ResponseModel[Product](content=product)
order = Order(id=1, product=response)
print(repr(order))
"""
Order(id=1, product=ResponseModel[Product](content=Product(name='Apple', price=0.5)))
"""
```

Using the same type variable in nested models allows you to enforce typing relationships at different points in your model:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar('T')

class InnerT(BaseModel, Generic[T]):
    inner: T

class OuterT(BaseModel, Generic[T]):
    outer: T
    nested: InnerT[T]

nested = InnerT[int](inner=1)
print(OuterT[int](outer=1, nested=nested))
#> outer=1 nested=InnerT[int](inner=1)
try:
    print(OuterT[int](outer='a', nested=InnerT(inner='a')))  
except ValidationError as e:
    print(e)
    """
    2 validation errors for OuterT[int]
    outer
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    nested.inner
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

Warning

While it may not raise an error, we strongly advise against using parametrized generics in [`isinstance()`](https://docs.python.org/3/library/functions.html#isinstance) checks.

For example, you should not do `isinstance(my_model, MyGenericModel[int])`. However, it is fine to do `isinstance(my_model, MyGenericModel)` (note that, for standard generics, it would raise an error to do a subclass check with a parameterized generic class).

If you need to perform [`isinstance()`](https://docs.python.org/3/library/functions.html#isinstance) checks against parametrized generics, you can do this by subclassing the parametrized generic class:

```python
class MyIntModel(MyGenericModel[int]): ...

isinstance(my_model, MyIntModel)
```

Implementation Details

When using nested generic models, Pydantic sometimes performs revalidation in an attempt to produce the most intuitive validation result. Specifically, if you have a field of type `GenericModel[SomeType]` and you validate data like `GenericModel[SomeCompatibleType]` against this field, we will inspect the data, recognize that the input data is sort of a "loose" subclass of `GenericModel`, and revalidate the contained `SomeCompatibleType` data.

This adds some validation overhead, but makes things more intuitive for cases like that shown below.

```python
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')

class GenericModel(BaseModel, Generic[T]):
    a: T

class Model(BaseModel):
    inner: GenericModel[Any]

print(repr(Model.model_validate(Model(inner=GenericModel[int](a=1)))))
#> Model(inner=GenericModel[Any](a=1))
```

Note, validation will still fail if you, for example are validating against `GenericModel[int]` and pass in an instance `GenericModel[str](a='not an int')`.

It's also worth noting that this pattern will re-trigger any custom validation as well, like additional model validators and the like. Validators will be called once on the first pass, validating directly against `GenericModel[Any]`. That validation fails, as `GenericModel[int]` is not a subclass of `GenericModel[Any]`. This relates to the warning above about the complications of using parametrized generics in `isinstance()` and `issubclass()` checks. Then, the validators will be called again on the second pass, during more lax force-revalidation phase, which succeeds. To better understand this consequence, see below:

```python
from typing import Any, Generic, Self, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar('T')

class GenericModel(BaseModel, Generic[T]):
    a: T

    @model_validator(mode='after')
    def validate_after(self: Self) -> Self:
        print('after validator running custom validation...')
        return self

class Model(BaseModel):
    inner: GenericModel[Any]

m = Model.model_validate(Model(inner=GenericModel[int](a=1)))
#> after validator running custom validation...
#> after validator running custom validation...
print(repr(m))
#> Model(inner=GenericModel[Any](a=1))
```
### Validation of unparametrized type variables¶

When leaving type variables unparametrized, Pydantic treats generic models similarly to how it treats built-in generic types like [`list`](https://docs.python.org/3/glossary.html#term-list) and [`dict`](https://docs.python.org/3/reference/expressions.html#dict):

- If the type variable is [bound](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-upper-bounds) or [constrained](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-constraints) to a specific type, it will be used.
- If the type variable has a default type (as specified by [PEP 696](https://peps.python.org/pep-0696/)), it will be used.
- For unbound or unconstrained type variables, Pydantic will fallback to [`Any`](https://docs.python.org/3/library/typing.html#typing.Any).

```python
from typing import Generic

from typing_extensions import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar('T')
U = TypeVar('U', bound=int)
V = TypeVar('V', default=str)

class Model(BaseModel, Generic[T, U, V]):
    t: T
    u: U
    v: V

print(Model(t='t', u=1, v='v'))
#> t='t' u=1 v='v'

try:
    Model(t='t', u='u', v=1)
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for Model
    u
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='u', input_type=str]
    v
      Input should be a valid string [type=string_type, input_value=1, input_type=int]
    """
```

Warning

In some cases, validation against an unparametrized generic model can lead to data loss. Specifically, if a subtype of the type variable upper bound, constraints, or default is being used and the model isn't explicitly parametrized, the resulting type **will not be** the one being provided:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

ItemT = TypeVar('ItemT', bound='ItemBase')

class ItemBase(BaseModel): ...

class IntItem(ItemBase):
    value: int

class ItemHolder(BaseModel, Generic[ItemT]):
    item: ItemT

loaded_data = {'item': {'value': 1}}

print(ItemHolder(**loaded_data))  
#> item=ItemBase()

print(ItemHolder[IntItem](**loaded_data))  
#> item=IntItem(value=1)
```

### Serialization of unparametrized type variables¶

The behavior of serialization differs when using type variables with [upper bounds](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-upper-bounds), [constraints](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-constraints), or a default value:

If a Pydantic model is used in a type variable upper bound and the type variable is never parametrized, then Pydantic will use the upper bound for validation but treat the value as [`Any`](https://docs.python.org/3/library/typing.html#typing.Any) in terms of serialization:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

class ErrorDetails(BaseModel):
    foo: str

ErrorDataT = TypeVar('ErrorDataT', bound=ErrorDetails)

class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: ErrorDataT

class MyErrorDetails(ErrorDetails):
    bar: str

# serialized as Any
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'var2',
    },
}

# serialized using the concrete parametrization
# note that \`'bar': 'var2'\` is missing
error = Error[ErrorDetails](
    message='We just had an error',
    details=ErrorDetails(foo='var'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}
```

Here's another example of the above behavior, enumerating all permutations regarding bound specification and generic type parametrization:

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

TBound = TypeVar('TBound', bound=BaseModel)
TNoBound = TypeVar('TNoBound')

class IntValue(BaseModel):
    value: int

class ItemBound(BaseModel, Generic[TBound]):
    item: TBound

class ItemNoBound(BaseModel, Generic[TNoBound]):
    item: TNoBound

item_bound_inferred = ItemBound(item=IntValue(value=3))
item_bound_explicit = ItemBound[IntValue](item=IntValue(value=3))
item_no_bound_inferred = ItemNoBound(item=IntValue(value=3))
item_no_bound_explicit = ItemNoBound[IntValue](item=IntValue(value=3))

# calling \`print(x.model_dump())\` on any of the above instances results in the following:
#> {'item': {'value': 3}}
```

However, if [constraints](https://typing.readthedocs.io/en/latest/reference/generics.html#type-variables-with-constraints) or a default value (as per [PEP 696](https://peps.python.org/pep-0696/)) is being used, then the default type or constraints will be used for both validation and serialization if the type variable is not parametrized. You can override this behavior using [`SerializeAsAny`](https://docs.pydantic.dev/latest/concepts/serialization/#serializeasany-annotation):

```
from typing import Generic

from typing_extensions import TypeVar

from pydantic import BaseModel, SerializeAsAny

class ErrorDetails(BaseModel):
    foo: str

ErrorDataT = TypeVar('ErrorDataT', default=ErrorDetails)

class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: ErrorDataT

class MyErrorDetails(ErrorDetails):
    bar: str

# serialized using the default's serializer
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}
# If \`ErrorDataT\` was using an upper bound, \`bar\` would be present in \`details\`.

class SerializeAsAnyError(BaseModel, Generic[ErrorDataT]):
    message: str
    details: SerializeAsAny[ErrorDataT]

# serialized as Any
error = SerializeAsAnyError(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='baz'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'baz',
    },
}
```

```
from typing import Generic

from typing import TypeVar

from pydantic import BaseModel, SerializeAsAny

class ErrorDetails(BaseModel):
    foo: str

ErrorDataT = TypeVar('ErrorDataT', default=ErrorDetails)

class Error(BaseModel, Generic[ErrorDataT]):
    message: str
    details: ErrorDataT

class MyErrorDetails(ErrorDetails):
    bar: str

# serialized using the default's serializer
error = Error(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='var2'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
    },
}
# If \`ErrorDataT\` was using an upper bound, \`bar\` would be present in \`details\`.

class SerializeAsAnyError(BaseModel, Generic[ErrorDataT]):
    message: str
    details: SerializeAsAny[ErrorDataT]

# serialized as Any
error = SerializeAsAnyError(
    message='We just had an error',
    details=MyErrorDetails(foo='var', bar='baz'),
)
assert error.model_dump() == {
    'message': 'We just had an error',
    'details': {
        'foo': 'var',
        'bar': 'baz',
    },
}
```

## Dynamic model creation¶
API Documentation

[`pydantic.main.create_model`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.create_model)  

There are some occasions where it is desirable to create a model using runtime information to specify the fields. Pydantic provides the [`create_model()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.create_model) function to allow models to be created dynamically:

```python
from pydantic import BaseModel, create_model

DynamicFoobarModel = create_model('DynamicFoobarModel', foo=str, bar=(int, 123))

# Equivalent to:

class StaticFoobarModel(BaseModel):
    foo: str
    bar: int = 123
```

Field definitions are specified as keyword arguments, and should either be:

- A single element, representing the type annotation of the field.
- A two-tuple, the first element being the type and the second element the assigned value (either a default or the [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) function).

Here is a more advanced example:

```python
from typing import Annotated

from pydantic import BaseModel, Field, PrivateAttr, create_model

DynamicModel = create_model(
    'DynamicModel',
    foo=(str, Field(alias='FOO')),
    bar=Annotated[str, Field(description='Bar field')],
    _private=(int, PrivateAttr(default=1)),
)

class StaticModel(BaseModel):
    foo: str = Field(alias='FOO')
    bar: Annotated[str, Field(description='Bar field')]
    _private: int = PrivateAttr(default=1)
```

The special keyword arguments `__config__` and `__base__` can be used to customize the new model. This includes extending a base model with extra fields.

```python
from pydantic import BaseModel, create_model

class FooModel(BaseModel):
    foo: str
    bar: int = 123

BarModel = create_model(
    'BarModel',
    apple=(str, 'russet'),
    banana=(str, 'yellow'),
    __base__=FooModel,
)
print(BarModel)
#> <class '__main__.BarModel'>
print(BarModel.model_fields.keys())
#> dict_keys(['foo', 'bar', 'apple', 'banana'])
```

You can also add validators by passing a dictionary to the `__validators__` argument.

```python
from pydantic import ValidationError, create_model, field_validator

def alphanum(cls, v):
    assert v.isalnum(), 'must be alphanumeric'
    return v

validators = {
    'username_validator': field_validator('username')(alphanum)  
}

UserModel = create_model(
    'UserModel', username=(str, ...), __validators__=validators
)

user = UserModel(username='scolvin')
print(user)
#> username='scolvin'

try:
    UserModel(username='scolvi%n')
except ValidationError as e:
    print(e)
    """
    1 validation error for UserModel
    username
      Assertion failed, must be alphanumeric [type=assertion_error, input_value='scolvi%n', input_type=str]
    """
```

Note

To pickle a dynamically created model:

- the model must be defined globally
- the `__module__` argument must be provided

## `RootModel` and custom root types[¶](https://docs.pydantic.dev/latest/concepts/models/#rootmodel-and-custom-root-types "Permanent link")

API Documentation

[`pydantic.root_model.RootModel`](https://docs.pydantic.dev/latest/api/root_model/#pydantic.root_model.RootModel)  

Pydantic models can be defined with a "custom root type" by subclassing [`pydantic.RootModel`](https://docs.pydantic.dev/latest/api/root_model/#pydantic.root_model.RootModel).

The root type can be any type supported by Pydantic, and is specified by the generic parameter to `RootModel`. The root value can be passed to the model `__init__` or [`model_validate`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate) via the first and only argument.

Here's an example of how this works:

```python
from pydantic import RootModel

Pets = RootModel[list[str]]
PetsByName = RootModel[dict[str, str]]

print(Pets(['dog', 'cat']))
#> root=['dog', 'cat']
print(Pets(['dog', 'cat']).model_dump_json())
#> ["dog","cat"]
print(Pets.model_validate(['dog', 'cat']))
#> root=['dog', 'cat']
print(Pets.model_json_schema())
"""
{'items': {'type': 'string'}, 'title': 'RootModel[list[str]]', 'type': 'array'}
"""

print(PetsByName({'Otis': 'dog', 'Milo': 'cat'}))
#> root={'Otis': 'dog', 'Milo': 'cat'}
print(PetsByName({'Otis': 'dog', 'Milo': 'cat'}).model_dump_json())
#> {"Otis":"dog","Milo":"cat"}
print(PetsByName.model_validate({'Otis': 'dog', 'Milo': 'cat'}))
#> root={'Otis': 'dog', 'Milo': 'cat'}
```

If you want to access items in the `root` field directly or to iterate over the items, you can implement custom `__iter__` and `__getitem__` functions, as shown in the following example.

```python
from pydantic import RootModel

class Pets(RootModel):
    root: list[str]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

pets = Pets.model_validate(['dog', 'cat'])
print(pets[0])
#> dog
print([pet for pet in pets])
#> ['dog', 'cat']
```

You can also create subclasses of the parametrized root model directly:

```python
from pydantic import RootModel

class Pets(RootModel[list[str]]):
    def describe(self) -> str:
        return f'Pets: {", ".join(self.root)}'

my_pets = Pets.model_validate(['dog', 'cat'])

print(my_pets.describe())
#> Pets: dog, cat
```

## Faux immutability¶

Models can be configured to be immutable via `model_config['frozen'] = True`. When this is set, attempting to change the values of instance attributes will raise errors. See the [API reference](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.frozen) for more details.

Note

This behavior was achieved in Pydantic V1 via the config setting `allow_mutation = False`. This config flag is deprecated in Pydantic V2, and has been replaced with `frozen`.

Warning

In Python, immutability is not enforced. Developers have the ability to modify objects that are conventionally considered "immutable" if they choose to do so.

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class FooBarModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: str
    b: dict

foobar = FooBarModel(a='hello', b={'apple': 'pear'})

try:
    foobar.a = 'different'
except ValidationError as e:
    print(e)
    """
    1 validation error for FooBarModel
    a
      Instance is frozen [type=frozen_instance, input_value='different', input_type=str]
    """

print(foobar.a)
#> hello
print(foobar.b)
#> {'apple': 'pear'}
foobar.b['apple'] = 'grape'
print(foobar.b)
#> {'apple': 'grape'}
```

Trying to change `a` caused an error, and `a` remains unchanged. However, the dict `b` is mutable, and the immutability of `foobar` doesn't stop `b` from being changed.

## Abstract base classes¶

Pydantic models can be used alongside Python's [Abstract Base Classes](https://docs.python.org/3/library/abc.html) (ABCs).

```python
import abc

from pydantic import BaseModel

class FooBarModel(BaseModel, abc.ABC):
    a: str
    b: int

    @abc.abstractmethod
    def my_abstract_method(self):
        pass
```

## Field ordering¶

Field order affects models in the following ways:

- field order is preserved in the model [JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)
- field order is preserved in [validation errors](https://docs.pydantic.dev/latest/concepts/models/#error-handling)
- field order is preserved by [`.model_dump()` and `.model_dump_json()` etc.](https://docs.pydantic.dev/latest/concepts/serialization/#model_dump)

```python
from pydantic import BaseModel, ValidationError

class Model(BaseModel):
    a: int
    b: int = 2
    c: int = 1
    d: int = 0
    e: float

print(Model.model_fields.keys())
#> dict_keys(['a', 'b', 'c', 'd', 'e'])
m = Model(e=2, a=1)
print(m.model_dump())
#> {'a': 1, 'b': 2, 'c': 1, 'd': 0, 'e': 2.0}
try:
    Model(a='x', b='x', c='x', d='x', e='x')
except ValidationError as err:
    error_locations = [e['loc'] for e in err.errors()]

print(error_locations)
#> [('a',), ('b',), ('c',), ('d',), ('e',)]
```

## Automatically excluded attributes¶
### Class variables¶

Attributes annotated with [`ClassVar`](https://docs.python.org/3/library/typing.html#typing.ClassVar) are properly treated by Pydantic as class variables, and will not become fields on model instances:

```python
from typing import ClassVar

from pydantic import BaseModel

class Model(BaseModel):
    x: ClassVar[int] = 1

    y: int = 2

m = Model()
print(m)
#> y=2
print(Model.x)
#> 1
```

### Private model attributes¶
API Documentation

[`pydantic.fields.PrivateAttr`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.PrivateAttr)  

Attributes whose name has a leading underscore are not treated as fields by Pydantic, and are not included in the model schema. Instead, these are converted into a "private attribute" which is not validated or even set during calls to `__init__`, `model_validate`, etc.

Here is an example of usage:

```python
from datetime import datetime
from random import randint
from typing import Any

from pydantic import BaseModel, PrivateAttr

class TimeAwareModel(BaseModel):
    _processed_at: datetime = PrivateAttr(default_factory=datetime.now)
    _secret_value: str

    def model_post_init(self, context: Any) -> None:
        # this could also be done with \`default_factory\`:
        self._secret_value = randint(1, 5)

m = TimeAwareModel()
print(m._processed_at)
#> 2032-01-02 03:04:05.000006
print(m._secret_value)
#> 3
```

Private attribute names must start with underscore to prevent conflicts with model fields. However, dunder names (such as `__attr__`) are not supported, and will be completely ignored from the model definition.

## Model signature¶

All Pydantic models will have their signature generated based on their fields:

```python
import inspect

from pydantic import BaseModel, Field

class FooModel(BaseModel):
    id: int
    name: str = None
    description: str = 'Foo'
    apple: int = Field(alias='pear')

print(inspect.signature(FooModel))
#> (*, id: int, name: str = None, description: str = 'Foo', pear: int) -> None
```

An accurate signature is useful for introspection purposes and libraries like `FastAPI` or `hypothesis`.

The generated signature will also respect custom `__init__` functions:

```python
import inspect

from pydantic import BaseModel

class MyModel(BaseModel):
    id: int
    info: str = 'Foo'

    def __init__(self, id: int = 1, *, bar: str, **data) -> None:
        """My custom init!"""
        super().__init__(id=id, bar=bar, **data)

print(inspect.signature(MyModel))
#> (id: int = 1, *, bar: str, info: str = 'Foo') -> None
```

To be included in the signature, a field's alias or name must be a valid Python identifier. Pydantic will prioritize a field's alias over its name when generating the signature, but may use the field name if the alias is not a valid Python identifier.

If a field's alias and name are *both* not valid identifiers (which may be possible through exotic use of `create_model`), a `**data` argument will be added. In addition, the `**data` argument will always be present in the signature if `model_config['extra'] == 'allow'`.

## Structural pattern matching¶

Pydantic supports structural pattern matching for models, as introduced by [PEP 636](https://peps.python.org/pep-0636/) in Python 3.10.

```python
from pydantic import BaseModel

class Pet(BaseModel):
    name: str
    species: str

a = Pet(name='Bones', species='dog')

match a:
    # match \`species\` to 'dog', declare and initialize \`dog_name\`
    case Pet(species='dog', name=dog_name):
        print(f'{dog_name} is a dog')
#> Bones is a dog
    # default case
    case _:
        print('No dog matched')
```

Note

A match-case statement may seem as if it creates a new model, but don't be fooled; it is just syntactic sugar for getting an attribute and either comparing it or declaring and initializing it.

## Attribute copies¶

In many cases, arguments passed to the constructor will be copied in order to perform validation and, where necessary, coercion.

In this example, note that the ID of the list changes after the class is constructed because it has been copied during validation:

```python
from pydantic import BaseModel

class C1:
    arr = []

    def __init__(self, in_arr):
        self.arr = in_arr

class C2(BaseModel):
    arr: list[int]

arr_orig = [1, 9, 10, 3]

c1 = C1(arr_orig)
c2 = C2(arr=arr_orig)
print(f'{id(c1.arr) == id(c2.arr)=}')
#> id(c1.arr) == id(c2.arr)=False
```

---
title: "Fields - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/fields/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
API Documentation

[`pydantic.fields.Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field)  

In this section, we will go through the available mechanisms to customize Pydantic model fields: default values, JSON Schema metadata, constraints, etc.

To do so, the [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) function is used a lot, and behaves the same way as the standard library [`field()`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field) function for dataclasses:

```python
from pydantic import BaseModel, Field

class Model(BaseModel):
    name: str = Field(frozen=True)
```

Note

Even though `name` is assigned a value, it is still required and has no default value. If you want to emphasize on the fact that a value must be provided, you can use the [ellipsis](https://docs.python.org/3/library/constants.html#Ellipsis):

```python
class Model(BaseModel):
    name: str = Field(..., frozen=True)
```

However, its usage is discouraged as it doesn't play well with static type checkers.

## The annotated pattern¶

To apply constraints or attach [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) functions to a model field, Pydantic supports the [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) typing construct to attach metadata to an annotation:

```python
from typing import Annotated

from pydantic import BaseModel, Field, WithJsonSchema

class Model(BaseModel):
    name: Annotated[str, Field(strict=True), WithJsonSchema({'extra': 'data'})]
```

As far as static type checkers are concerned, `name` is still typed as `str`, but Pydantic leverages the available metadata to add validation logic, type constraints, etc.

Using this pattern has some advantages:

- Using the `f: <type> = Field(...)` form can be confusing and might trick users into thinking `f` has a default value, while in reality it is still required.
- You can provide an arbitrary amount of metadata elements for a field. As shown in the example above, the [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) function only supports a limited set of constraints/metadata, and you may have to use different Pydantic utilities such as [`WithJsonSchema`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema.WithJsonSchema) in some cases.
- Types can be made reusable (see the documentation on [custom types](https://docs.pydantic.dev/latest/concepts/types/#using-the-annotated-pattern) using this pattern).

However, note that certain arguments to the [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) function (namely, `default`, `default_factory`, and `alias`) are taken into account by static type checkers to synthesize a correct `__init__` method. The annotated pattern is *not* understood by them, so you should use the normal assignment form instead.

Tip

The annotated pattern can also be used to add metadata to specific parts of the type. For instance, [validation constraints](https://docs.pydantic.dev/latest/concepts/fields/#field-constraints) can be added this way:

```python
from typing import Annotated

from pydantic import BaseModel, Field

class Model(BaseModel):
    int_list: list[Annotated[int, Field(gt=0)]]
    # Valid: [1, 3]
    # Invalid: [-1, 2]
```

## Default values¶

Default values for fields can be provided using the normal assignment syntax or by providing a value to the `default` argument:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    # Both fields aren't required:
    name: str = 'John Doe'
    age: int = Field(default=20)
```

Warning

[In Pydantic V1](https://docs.pydantic.dev/latest/migration/#required-optional-and-nullable-fields), a type annotated as [`Any`](https://docs.python.org/3/library/typing.html#typing.Any) or wrapped by [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional) would be given an implicit default of `None` even if no default was explicitly specified. This is no longer the case in Pydantic V2.

You can also pass a callable to the `default_factory` argument that will be called to generate a default value:

```python
from uuid import uuid4

from pydantic import BaseModel, Field

class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
```

The default factory can also take a single required argument, in which case the already validated data will be passed as a dictionary.

```python
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    email: EmailStr
    username: str = Field(default_factory=lambda data: data['email'])

user = User(email='user@example.com')
print(user.username)
#> user@example.com
```

The `data` argument will *only* contain the already validated data, based on the [order of model fields](https://docs.pydantic.dev/latest/concepts/models/#field-ordering) (the above example would fail if `username` were to be defined before `email`).

## Validate default values¶

By default, Pydantic will *not* validate default values. The `validate_default` field parameter (or the [`validate_default`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.validate_default) configuration value) can be used to enable this behavior:

```python
from pydantic import BaseModel, Field, ValidationError

class User(BaseModel):
    age: int = Field(default='twelve', validate_default=True)

try:
    user = User()
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='twelve', input_type=str]
    """
```

### Mutable default values¶

A common source of bugs in Python is to use a mutable object as a default value for a function or method argument, as the same instance ends up being reused in each call.

The [`dataclasses`](https://docs.python.org/3/library/dataclasses.html#module-dataclasses) module actually raises an error in this case, indicating that you should use a [default factory](https://docs.python.org/3/library/dataclasses.html#default-factory-functions) instead.

While the same thing can be done in Pydantic, it is not required. In the event that the default value is not hashable, Pydantic will create a deep copy of the default value when creating each instance of the model:

```python
from pydantic import BaseModel

class Model(BaseModel):
    item_counts: list[dict[str, int]] = [{}]

m1 = Model()
m1.item_counts[0]['a'] = 1
print(m1.item_counts)
#> [{'a': 1}]

m2 = Model()
print(m2.item_counts)
#> [{}]
```

## Field aliases¶

For validation and serialization, you can define an alias for a field.

There are three ways to define an alias:

- `Field(alias='foo')`
- `Field(validation_alias='foo')`
- `Field(serialization_alias='foo')`

The `alias` parameter is used for both validation *and* serialization. If you want to use *different* aliases for validation and serialization respectively, you can use the `validation_alias` and `serialization_alias` parameters, which will apply only in their respective use cases.

Here is an example of using the `alias` parameter:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(alias='username')

user = User(username='johndoe')  
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  
#> {'username': 'johndoe'}
```

If you want to use an alias *only* for validation, you can use the `validation_alias` parameter:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(validation_alias='username')

user = User(username='johndoe')  
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  
#> {'name': 'johndoe'}
```

If you only want to define an alias for *serialization*, you can use the `serialization_alias` parameter:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(serialization_alias='username')

user = User(name='johndoe')  
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  
#> {'username': 'johndoe'}
```

Alias precedence and priority

In case you use `alias` together with `validation_alias` or `serialization_alias` at the same time, the `validation_alias` will have priority over `alias` for validation, and `serialization_alias` will have priority over `alias` for serialization.

If you provide a value for the [`alias_generator`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.alias_generator) model setting, you can control the order of precedence for field alias and generated aliases via the `alias_priority` field parameter. You can read more about alias precedence [here](https://docs.pydantic.dev/latest/concepts/alias/#alias-precedence).

Static type checking/IDE support

If you provide a value for the `alias` field parameter, static type checkers will use this alias instead of the actual field name to synthesize the `__init__` method:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(alias='username')

user = User(username='johndoe')  
```

This means that when using the [`validate_by_name`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.validate_by_name) model setting (which allows both the field name and alias to be used during model validation), type checkers will error when the actual field name is used:

```python
from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    model_config = ConfigDict(validate_by_name=True)

    name: str = Field(alias='username')

user = User(name='johndoe')  
```

If you still want type checkers to use the field name and not the alias, the [annotated pattern](https://docs.pydantic.dev/latest/concepts/fields/#the-annotated-pattern) can be used (which is only understood by Pydantic):

```python
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    name: Annotated[str, Field(alias='username')]

user = User(name='johndoe')  
user = User(username='johndoe')  
```

### Validation Alias

Even though Pydantic treats `alias` and `validation_alias` the same when creating model instances, type checkers only understand the `alias` field parameter. As a workaround, you can instead specify both an `alias` and serialization\_alias`(identical to the field name), as the`serialization\_alias`will override the`alias\` during serialization:

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    my_field: int = Field(validation_alias='myValidationAlias')
```

with:

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    my_field: int = Field(
        alias='myValidationAlias',
        serialization_alias='my_field',
    )

m = MyModel(myValidationAlias=1)
print(m.model_dump(by_alias=True))
#> {'my_field': 1}
```
## Numeric Constraints¶

There are some keyword arguments that can be used to constrain numeric values:

- `gt` - greater than
- `lt` - less than
- `ge` - greater than or equal to
- `le` - less than or equal to
- `multiple_of` - a multiple of the given number
- `allow_inf_nan` - allow `'inf'`, `'-inf'`, `'nan'` values

Here's an example:

```python
from pydantic import BaseModel, Field

class Foo(BaseModel):
    positive: int = Field(gt=0)
    non_negative: int = Field(ge=0)
    negative: int = Field(lt=0)
    non_positive: int = Field(le=0)
    even: int = Field(multiple_of=2)
    love_for_pydantic: float = Field(allow_inf_nan=True)

foo = Foo(
    positive=1,
    non_negative=0,
    negative=-1,
    non_positive=0,
    even=2,
    love_for_pydantic=float('inf'),
)
print(foo)
"""
positive=1 non_negative=0 negative=-1 non_positive=0 even=2 love_for_pydantic=inf
"""
```

JSON Schema

In the generated JSON schema:

- `gt` and `lt` constraints will be translated to `exclusiveMinimum` and `exclusiveMaximum`.
- `ge` and `le` constraints will be translated to `minimum` and `maximum`.
- `multiple_of` constraint will be translated to `multipleOf`.

The above snippet will generate the following JSON Schema:

```json
{
  "title": "Foo",
  "type": "object",
  "properties": {
    "positive": {
      "title": "Positive",
      "type": "integer",
      "exclusiveMinimum": 0
    },
    "non_negative": {
      "title": "Non Negative",
      "type": "integer",
      "minimum": 0
    },
    "negative": {
      "title": "Negative",
      "type": "integer",
      "exclusiveMaximum": 0
    },
    "non_positive": {
      "title": "Non Positive",
      "type": "integer",
      "maximum": 0
    },
    "even": {
      "title": "Even",
      "type": "integer",
      "multipleOf": 2
    },
    "love_for_pydantic": {
      "title": "Love For Pydantic",
      "type": "number"
    }
  },
  "required": [
    "positive",
    "non_negative",
    "negative",
    "non_positive",
    "even",
    "love_for_pydantic"
  ]
}
```

See the [JSON Schema Draft 2020-12](https://json-schema.org/understanding-json-schema/reference/numeric.html#numeric-types) for more details.

Constraints on compound types

In case you use field constraints with compound types, an error can happen in some cases. To avoid potential issues, you can use `Annotated`:

```python
from typing import Annotated, Optional

from pydantic import BaseModel, Field

class Foo(BaseModel):
    positive: Optional[Annotated[int, Field(gt=0)]]
    # Can error in some cases, not recommended:
    non_negative: Optional[int] = Field(ge=0)
```

## String Constraints¶
API Documentation

[`pydantic.types.StringConstraints`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StringConstraints)  

There are fields that can be used to constrain strings:

- `min_length`: Minimum length of the string.
- `max_length`: Maximum length of the string.
- `pattern`: A regular expression that the string must match.

Here's an example:

```python
from pydantic import BaseModel, Field

class Foo(BaseModel):
    short: str = Field(min_length=3)
    long: str = Field(max_length=10)
    regex: str = Field(pattern=r'^\d*$')  

foo = Foo(short='foo', long='foobarbaz', regex='123')
print(foo)
#> short='foo' long='foobarbaz' regex='123'
```

JSON Schema

In the generated JSON schema:

- `min_length` constraint will be translated to `minLength`.
- `max_length` constraint will be translated to `maxLength`.
- `pattern` constraint will be translated to `pattern`.

The above snippet will generate the following JSON Schema:

```json
{
  "title": "Foo",
  "type": "object",
  "properties": {
    "short": {
      "title": "Short",
      "type": "string",
      "minLength": 3
    },
    "long": {
      "title": "Long",
      "type": "string",
      "maxLength": 10
    },
    "regex": {
      "title": "Regex",
      "type": "string",
      "pattern": "^\\d*$"
    }
  },
  "required": [
    "short",
    "long",
    "regex"
  ]
}
```
## Decimal Constraints¶

There are fields that can be used to constrain decimals:

- `max_digits`: Maximum number of digits within the `Decimal`. It does not include a zero before the decimal point or trailing decimal zeroes.
- `decimal_places`: Maximum number of decimal places allowed. It does not include trailing decimal zeroes.

Here's an example:

```python
from decimal import Decimal

from pydantic import BaseModel, Field

class Foo(BaseModel):
    precise: Decimal = Field(max_digits=5, decimal_places=2)

foo = Foo(precise=Decimal('123.45'))
print(foo)
#> precise=Decimal('123.45')
```

## Dataclass Constraints¶

There are fields that can be used to constrain dataclasses:

- `init`: Whether the field should be included in the `__init__` of the dataclass.
- `init_var`: Whether the field should be seen as an [init-only field](https://docs.python.org/3/library/dataclasses.html#init-only-variables) in the dataclass.
- `kw_only`: Whether the field should be a keyword-only argument in the constructor of the dataclass.

Here's an example:

```python
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

@dataclass
class Foo:
    bar: str
    baz: str = Field(init_var=True)
    qux: str = Field(kw_only=True)

class Model(BaseModel):
    foo: Foo

model = Model(foo=Foo('bar', baz='baz', qux='qux'))
print(model.model_dump())  
#> {'foo': {'bar': 'bar', 'qux': 'qux'}}
```

## Field Representation¶

The parameter `repr` can be used to control whether the field should be included in the string representation of the model.

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(repr=True)  
    age: int = Field(repr=False)

user = User(name='John', age=42)
print(user)
#> name='John'
```

## Discriminator¶

The parameter `discriminator` can be used to control the field that will be used to discriminate between different models in a union. It takes either the name of a field or a `Discriminator` instance. The `Discriminator` approach can be useful when the discriminator fields aren't the same for all the models in the `Union`.

The following example shows how to use `discriminator` with a field name:

```
from typing import Literal, Union

from pydantic import BaseModel, Field

class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int

class Dog(BaseModel):
    pet_type: Literal['dog']
    age: int

class Model(BaseModel):
    pet: Union[Cat, Dog] = Field(discriminator='pet_type')

print(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}}))  
#> pet=Cat(pet_type='cat', age=12)
```

```python
from typing import Literal

from pydantic import BaseModel, Field

class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int

class Dog(BaseModel):
    pet_type: Literal['dog']
    age: int

class Model(BaseModel):
    pet: Cat | Dog = Field(discriminator='pet_type')

print(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}}))  
#> pet=Cat(pet_type='cat', age=12)
```

1. See more about [Validating data](https://docs.pydantic.dev/latest/concepts/models/#validating-data) in the [Models](https://docs.pydantic.dev/latest/concepts/models/) page.

The following example shows how to use the `discriminator` keyword argument with a `Discriminator` instance:

```
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Discriminator, Field, Tag

class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int

class Dog(BaseModel):
    pet_kind: Literal['dog']
    age: int

def pet_discriminator(v):
    if isinstance(v, dict):
        return v.get('pet_type', v.get('pet_kind'))
    return getattr(v, 'pet_type', getattr(v, 'pet_kind', None))

class Model(BaseModel):
    pet: Union[Annotated[Cat, Tag('cat')], Annotated[Dog, Tag('dog')]] = Field(
        discriminator=Discriminator(pet_discriminator)
    )

print(repr(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}})))
#> Model(pet=Cat(pet_type='cat', age=12))

print(repr(Model.model_validate({'pet': {'pet_kind': 'dog', 'age': 12}})))
#> Model(pet=Dog(pet_kind='dog', age=12))
```

```
from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator, Field, Tag

class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int

class Dog(BaseModel):
    pet_kind: Literal['dog']
    age: int

def pet_discriminator(v):
    if isinstance(v, dict):
        return v.get('pet_type', v.get('pet_kind'))
    return getattr(v, 'pet_type', getattr(v, 'pet_kind', None))

class Model(BaseModel):
    pet: Annotated[Cat, Tag('cat')] | Annotated[Dog, Tag('dog')] = Field(
        discriminator=Discriminator(pet_discriminator)
    )

print(repr(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}})))
#> Model(pet=Cat(pet_type='cat', age=12))

print(repr(Model.model_validate({'pet': {'pet_kind': 'dog', 'age': 12}})))
#> Model(pet=Dog(pet_kind='dog', age=12))
```

You can also take advantage of `Annotated` to define your discriminated unions. See the [Discriminated Unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions) docs for more details.

## Strict Mode¶

The `strict` parameter on a [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) specifies whether the field should be validated in "strict mode". In strict mode, Pydantic throws an error during validation instead of coercing data on the field where `strict=True`.

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(strict=True)
    age: int = Field(strict=False)  

user = User(name='John', age='42')  
print(user)
#> name='John' age=42
```

See [Strict Mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) for more details.

See [Conversion Table](https://docs.pydantic.dev/latest/concepts/conversion_table/) for more details on how Pydantic converts data in both strict and lax modes.

## Immutability¶

The parameter `frozen` is used to emulate the frozen dataclass behaviour. It is used to prevent the field from being assigned a new value after the model is created (immutability).

See the [frozen dataclass documentation](https://docs.python.org/3/library/dataclasses.html#frozen-instances) for more details.

```python
from pydantic import BaseModel, Field, ValidationError

class User(BaseModel):
    name: str = Field(frozen=True)
    age: int

user = User(name='John', age=42)

try:
    user.name = 'Jane'  
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Field is frozen [type=frozen_field, input_value='Jane', input_type=str]
    """
```

## Exclude¶

The `exclude` parameter can be used to control which fields should be excluded from the model when exporting the model.

See the following example:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    age: int = Field(exclude=True)

user = User(name='John', age=42)
print(user.model_dump())  
#> {'name': 'John'}
```

See the [Serialization](https://docs.pydantic.dev/latest/concepts/serialization/#model-and-field-level-include-and-exclude) section for more details.

## Deprecated fields¶

The `deprecated` parameter can be used to mark a field as being deprecated. Doing so will result in:

- a runtime deprecation warning emitted when accessing the field.
- `"deprecated": true` being set in the generated JSON schema.

You can set the `deprecated` parameter as one of:

- A string, which will be used as the deprecation message.
- An instance of the `warnings.deprecated` decorator (or the `typing_extensions` backport).
- A boolean, which will be used to mark the field as deprecated with a default `'deprecated'` deprecation message.

### `deprecated` as a string[¶](https://docs.pydantic.dev/latest/concepts/fields/#deprecated-as-a-string "Permanent link")

```python
from typing import Annotated

from pydantic import BaseModel, Field

class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated='This is deprecated')]

print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

### `deprecated` via the `warnings.deprecated` decorator[¶](https://docs.pydantic.dev/latest/concepts/fields/#deprecated-via-the-warningsdeprecated-decorator "Permanent link")

Note

You can only use the `deprecated` decorator in this way if you have `typing_extensions` >= 4.9.0 installed.

```python
import importlib.metadata
from typing import Annotated, deprecated

from packaging.version import Version

from pydantic import BaseModel, Field

if Version(importlib.metadata.version('typing_extensions')) >= Version('4.9'):

    class Model(BaseModel):
        deprecated_field: Annotated[int, deprecated('This is deprecated')]

        # Or explicitly using \`Field\`:
        alt_form: Annotated[
            int, Field(deprecated=deprecated('This is deprecated'))
        ]
```

### `deprecated` as a boolean[¶](https://docs.pydantic.dev/latest/concepts/fields/#deprecated-as-a-boolean "Permanent link")

```python
from typing import Annotated

from pydantic import BaseModel, Field

class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated=True)]

print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

Support for `category` and `stacklevel`

The current implementation of this feature does not take into account the `category` and `stacklevel` arguments to the `deprecated` decorator. This might land in a future version of Pydantic.

Accessing a deprecated field in validators

When accessing a deprecated field inside a validator, the deprecation warning will be emitted. You can use [`catch_warnings`](https://docs.python.org/3/library/warnings.html#warnings.catch_warnings) to explicitly ignore it:

```python
import warnings

from typing_extensions import Self

from pydantic import BaseModel, Field, model_validator

class Model(BaseModel):
    deprecated_field: int = Field(deprecated='This is deprecated')

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            self.deprecated_field = self.deprecated_field * 2
```

## Customizing JSON Schema¶

Some field parameters are used exclusively to customize the generated JSON schema. The parameters in question are:

- `title`
- `description`
- `examples`
- `json_schema_extra`

Read more about JSON schema customization / modification with fields in the [Customizing JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/#field-level-customization) section of the JSON schema docs.

## The `computed_field` decorator[¶](https://docs.pydantic.dev/latest/concepts/fields/#the-computed_field-decorator "Permanent link")

API Documentation

[`computed_field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.computed_field)  

The [`computed_field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.computed_field) decorator can be used to include [`property`](https://docs.python.org/3/library/functions.html#property) or [`cached_property`](https://docs.python.org/3/library/functools.html#functools.cached_property) attributes when serializing a model or dataclass. The property will also be taken into account in the JSON Schema (in serialization mode).

Note

Properties can be useful for fields that are computed from other fields, or for fields that are expensive to be computed (and thus, are cached if using [`cached_property`](https://docs.python.org/3/library/functools.html#functools.cached_property)).

However, note that Pydantic will *not* perform any additional logic on the wrapped property (validation, cache invalidation, etc.).

Here's an example of the JSON schema (in serialization mode) generated for a model with a computed field:

```python
from pydantic import BaseModel, computed_field

class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property  # (1)!
    def volume(self) -> float:
        return self.width * self.height * self.depth

print(Box.model_json_schema(mode='serialization'))
"""
{
    'properties': {
        'width': {'title': 'Width', 'type': 'number'},
        'height': {'title': 'Height', 'type': 'number'},
        'depth': {'title': 'Depth', 'type': 'number'},
        'volume': {'readOnly': True, 'title': 'Volume', 'type': 'number'},
    },
    'required': ['width', 'height', 'depth', 'volume'],
    'title': 'Box',
    'type': 'object',
}
"""
```

Here's an example using the `model_dump` method with a computed field:

```python
from pydantic import BaseModel, computed_field

class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property  
    def volume(self) -> float:
        return self.width * self.height * self.depth

b = Box(width=1, height=2, depth=3)
print(b.model_dump())
#> {'width': 1.0, 'height': 2.0, 'depth': 3.0, 'volume': 6.0}
```

As with regular fields, computed fields can be marked as being deprecated:

```python
from typing_extensions import deprecated

from pydantic import BaseModel, computed_field

class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property
    @deprecated("'volume' is deprecated")
    def volume(self) -> float:
        return self.width * self.height * self.depth
```
---
title: "JSON Schema - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/json_schema/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
API Documentation

[`pydantic.json_schema`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema)  

Pydantic allows automatic creation and customization of JSON schemas from models. The generated JSON schemas are compliant with the following specifications:

- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/release-notes.html)
- [OpenAPI Specification v3.1.0](https://github.com/OAI/OpenAPI-Specification).

## Generating JSON Schema¶

Use the following functions to generate JSON schema:

- [`BaseModel.model_json_schema`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_json_schema) returns a jsonable dict of a model's schema.
- [`TypeAdapter.json_schema`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter.json_schema) returns a jsonable dict of an adapted type's schema.

on the "jsonable" nature of JSON schema

Regarding the "jsonable" nature of the [`model_json_schema`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_json_schema) results, calling `json.dumps(m.model_json_schema())`on some `BaseModel` `m` returns a valid JSON string. Similarly, for [`TypeAdapter.json_schema`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter.json_schema), calling `json.dumps(TypeAdapter(<some_type>).json_schema())` returns a valid JSON string.

Tip

Pydantic offers support for both of:

1. [Customizing JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/#customizing-json-schema)
2. [Customizing the JSON Schema Generation Process](https://docs.pydantic.dev/latest/concepts/json_schema/#customizing-the-json-schema-generation-process)

The first approach generally has a more narrow scope, allowing for customization of the JSON schema for more specific cases and types. The second approach generally has a more broad scope, allowing for customization of the JSON schema generation process overall. The same effects can be achieved with either approach, but depending on your use case, one approach might offer a more simple solution than the other.

Here's an example of generating JSON schema from a `BaseModel`:

```python
import json
from enum import Enum
from typing import Annotated, Union

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class FooBar(BaseModel):
    count: int
    size: Union[float, None] = None

class Gender(str, Enum):
    male = 'male'
    female = 'female'
    other = 'other'
    not_given = 'not_given'

class MainModel(BaseModel):
    """
    This is the description of the main model
    """

    model_config = ConfigDict(title='Main')

    foo_bar: FooBar
    gender: Annotated[Union[Gender, None], Field(alias='Gender')] = None
    snap: int = Field(
        default=42,
        title='The Snap',
        description='this is the value of snap',
        gt=30,
        lt=50,
    )

main_model_schema = MainModel.model_json_schema()  # (1)!
print(json.dumps(main_model_schema, indent=2))  # (2)!
```

JSON output:

```json
{
  "$defs": {
    "FooBar": {
      "properties": {
        "count": {
          "title": "Count",
          "type": "integer"
        },
        "size": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Size"
        }
      },
      "required": [
        "count"
      ],
      "title": "FooBar",
      "type": "object"
    },
    "Gender": {
      "enum": [
        "male",
        "female",
        "other",
        "not_given"
      ],
      "title": "Gender",
      "type": "string"
    }
  },
  "description": "This is the description of the main model",
  "properties": {
    "foo_bar": {
      "$ref": "#/$defs/FooBar"
    },
    "Gender": {
      "anyOf": [
        {
          "$ref": "#/$defs/Gender"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "snap": {
      "default": 42,
      "description": "this is the value of snap",
      "exclusiveMaximum": 50,
      "exclusiveMinimum": 30,
      "title": "The Snap",
      "type": "integer"
    }
  },
  "required": [
    "foo_bar"
  ],
  "title": "Main",
  "type": "object"
}
```

1. This produces a "jsonable" dict of `MainModel`'s schema.
2. Calling `json.dumps` on the schema dict produces a JSON string.

```python
import json
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class FooBar(BaseModel):
    count: int
    size: float | None = None

class Gender(str, Enum):
    male = 'male'
    female = 'female'
    other = 'other'
    not_given = 'not_given'

class MainModel(BaseModel):
    """
    This is the description of the main model
    """

    model_config = ConfigDict(title='Main')

    foo_bar: FooBar
    gender: Annotated[Gender | None, Field(alias='Gender')] = None
    snap: int = Field(
        default=42,
        title='The Snap',
        description='this is the value of snap',
        gt=30,
        lt=50,
    )

main_model_schema = MainModel.model_json_schema()  # (1)!
print(json.dumps(main_model_schema, indent=2))  # (2)!
```

JSON output:

```json
{
  "$defs": {
    "FooBar": {
      "properties": {
        "count": {
          "title": "Count",
          "type": "integer"
        },
        "size": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Size"
        }
      },
      "required": [
        "count"
      ],
      "title": "FooBar",
      "type": "object"
    },
    "Gender": {
      "enum": [
        "male",
        "female",
        "other",
        "not_given"
      ],
      "title": "Gender",
      "type": "string"
    }
  },
  "description": "This is the description of the main model",
  "properties": {
    "foo_bar": {
      "$ref": "#/$defs/FooBar"
    },
    "Gender": {
      "anyOf": [
        {
          "$ref": "#/$defs/Gender"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "snap": {
      "default": 42,
      "description": "this is the value of snap",
      "exclusiveMaximum": 50,
      "exclusiveMinimum": 30,
      "title": "The Snap",
      "type": "integer"
    }
  },
  "required": [
    "foo_bar"
  ],
  "title": "Main",
  "type": "object"
}
```

1. This produces a "jsonable" dict of `MainModel`'s schema.
2. Calling `json.dumps` on the schema dict produces a JSON string.

The [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) class lets you create an object with methods for validating, serializing, and producing JSON schemas for arbitrary types. This serves as a complete replacement for `schema_of` in Pydantic V1 (which is now deprecated).

Here's an example of generating JSON schema from a [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter):

```python
from pydantic import TypeAdapter

adapter = TypeAdapter(list[int])
print(adapter.json_schema())
#> {'items': {'type': 'integer'}, 'type': 'array'}
```

You can also generate JSON schemas for combinations of [`BaseModel`s](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel) and [`TypeAdapter`s](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter), as shown in this example:

```python
import json
from typing import Union

from pydantic import BaseModel, TypeAdapter

class Cat(BaseModel):
    name: str
    color: str

class Dog(BaseModel):
    name: str
    breed: str

ta = TypeAdapter(Union[Cat, Dog])
ta_schema = ta.json_schema()
print(json.dumps(ta_schema, indent=2))
```

JSON output:

```json
{
  "$defs": {
    "Cat": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "color": {
          "title": "Color",
          "type": "string"
        }
      },
      "required": [
        "name",
        "color"
      ],
      "title": "Cat",
      "type": "object"
    },
    "Dog": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "breed": {
          "title": "Breed",
          "type": "string"
        }
      },
      "required": [
        "name",
        "breed"
      ],
      "title": "Dog",
      "type": "object"
    }
  },
  "anyOf": [
    {
      "$ref": "#/$defs/Cat"
    },
    {
      "$ref": "#/$defs/Dog"
    }
  ]
}
```

### Configuring the `JsonSchemaMode`[¶](https://docs.pydantic.dev/latest/concepts/json_schema/#configuring-the-jsonschemamode "Permanent link")

Specify the mode of JSON schema generation via the `mode` parameter in the [`model_json_schema`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_json_schema) and [`TypeAdapter.json_schema`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter.json_schema) methods. By default, the mode is set to `'validation'`, which produces a JSON schema corresponding to the model's validation schema.

The [`JsonSchemaMode`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema.JsonSchemaMode) is a type alias that represents the available options for the `mode` parameter:

- `'validation'`
- `'serialization'`

Here's an example of how to specify the `mode` parameter, and how it affects the generated JSON schema:

```python
from decimal import Decimal

from pydantic import BaseModel

class Model(BaseModel):
    a: Decimal = Decimal('12.34')

print(Model.model_json_schema(mode='validation'))
"""
{
    'properties': {
        'a': {
            'anyOf': [{'type': 'number'}, {'type': 'string'}],
            'default': '12.34',
            'title': 'A',
        }
    },
    'title': 'Model',
    'type': 'object',
}
"""

print(Model.model_json_schema(mode='serialization'))
"""
{
    'properties': {'a': {'default': '12.34', 'title': 'A', 'type': 'string'}},
    'title': 'Model',
    'type': 'object',
}
"""
```

## Customizing JSON Schema¶

The generated JSON schema can be customized at both the field level and model level via:

1. [Field-level customization](https://docs.pydantic.dev/latest/concepts/json_schema/#field-level-customization) with the [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) constructor
2. [Model-level customization](https://docs.pydantic.dev/latest/concepts/json_schema/#model-level-customization) with [`model_config`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict)

At both the field and model levels, you can use the `json_schema_extra` option to add extra information to the JSON schema. The [Using `json_schema_extra`](https://docs.pydantic.dev/latest/concepts/json_schema/#using-json_schema_extra) section below provides more details on this option.

For custom types, Pydantic offers other tools for customizing JSON schema generation:

1. [`WithJsonSchema` annotation](https://docs.pydantic.dev/latest/concepts/json_schema/#withjsonschema-annotation)
2. [`SkipJsonSchema` annotation](https://docs.pydantic.dev/latest/concepts/json_schema/#skipjsonschema-annotation)
3. [Implementing `__get_pydantic_core_schema__`](https://docs.pydantic.dev/latest/concepts/json_schema/#implementing_get_pydantic_core_schema)
4. [Implementing `__get_pydantic_json_schema__`](https://docs.pydantic.dev/latest/concepts/json_schema/#implementing_get_pydantic_json_schema)

### Field-Level Customization¶

Optionally, the [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) function can be used to provide extra information about the field and validations.

Some field parameters are used exclusively to customize the generated JSON Schema:

- `title`: The title of the field.
- `description`: The description of the field.
- `examples`: The examples of the field.
- `json_schema_extra`: Extra JSON Schema properties to be added to the field.
- `field_title_generator`: A function that programmatically sets the field's title, based on its name and info.

Here's an example:

```python
import json

from pydantic import BaseModel, EmailStr, Field, SecretStr

class User(BaseModel):
    age: int = Field(description='Age of the user')
    email: EmailStr = Field(examples=['marcelo@mail.com'])
    name: str = Field(title='Username')
    password: SecretStr = Field(
        json_schema_extra={
            'title': 'Password',
            'description': 'Password of the user',
            'examples': ['123456'],
        }
    )

print(json.dumps(User.model_json_schema(), indent=2))
```

JSON output:

```json
{
  "properties": {
    "age": {
      "description": "Age of the user",
      "title": "Age",
      "type": "integer"
    },
    "email": {
      "examples": [
        "marcelo@mail.com"
      ],
      "format": "email",
      "title": "Email",
      "type": "string"
    },
    "name": {
      "title": "Username",
      "type": "string"
    },
    "password": {
      "description": "Password of the user",
      "examples": [
        "123456"
      ],
      "format": "password",
      "title": "Password",
      "type": "string",
      "writeOnly": true
    }
  },
  "required": [
    "age",
    "email",
    "name",
    "password"
  ],
  "title": "User",
  "type": "object"
}
```

#### Unenforced `Field` constraints[¶](https://docs.pydantic.dev/latest/concepts/json_schema/#unenforced-field-constraints "Permanent link")

If Pydantic finds constraints which are not being enforced, an error will be raised. If you want to force the constraint to appear in the schema, even though it's not being checked upon parsing, you can use variadic arguments to [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) with the raw schema attribute name:

```python
from pydantic import BaseModel, Field, PositiveInt

try:
    # this won't work since \`PositiveInt\` takes precedence over the
    # constraints defined in \`Field\`, meaning they're ignored
    class Model(BaseModel):
        foo: PositiveInt = Field(lt=10)

except ValueError as e:
    print(e)

# if you find yourself needing this, an alternative is to declare
# the constraints in \`Field\` (or you could use \`conint()\`)
# here both constraints will be enforced:
class ModelB(BaseModel):
    # Here both constraints will be applied and the schema
    # will be generated correctly
    foo: int = Field(gt=0, lt=10)

print(ModelB.model_json_schema())
"""
{
    'properties': {
        'foo': {
            'exclusiveMaximum': 10,
            'exclusiveMinimum': 0,
            'title': 'Foo',
            'type': 'integer',
        }
    },
    'required': ['foo'],
    'title': 'ModelB',
    'type': 'object',
}
"""
```

You can specify JSON schema modifications via the [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) constructor via [`typing.Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) as well:

```python
import json
from typing import Annotated
from uuid import uuid4

from pydantic import BaseModel, Field

class Foo(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
    name: Annotated[str, Field(max_length=256)] = Field(
        'Bar', title='CustomName'
    )

print(json.dumps(Foo.model_json_schema(), indent=2))
```

JSON output:

```json
{
  "properties": {
    "id": {
      "title": "Id",
      "type": "string"
    },
    "name": {
      "default": "Bar",
      "maxLength": 256,
      "title": "CustomName",
      "type": "string"
    }
  },
  "title": "Foo",
  "type": "object"
}
```

### Programmatic field title generation¶

The `field_title_generator` parameter can be used to programmatically generate the title for a field based on its name and info.

See the following example:

```python
import json

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

def make_title(field_name: str, field_info: FieldInfo) -> str:
    return field_name.upper()

class Person(BaseModel):
    name: str = Field(field_title_generator=make_title)
    age: int = Field(field_title_generator=make_title)

print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "properties": {
    "name": {
      "title": "NAME",
      "type": "string"
    },
    "age": {
      "title": "AGE",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Person",
  "type": "object"
}
"""
```

### Model-Level Customization¶

You can also use [model config](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict) to customize JSON schema generation on a model. Specifically, the following config options are relevant:

- [`title`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.title)
- [`json_schema_extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.json_schema_extra)
- [`json_schema_mode_override`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.json_schema_mode_override)
- [`field_title_generator`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.field_title_generator)
- [`model_title_generator`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.model_title_generator)

The `json_schema_extra` option can be used to add extra information to the JSON schema, either at the [Field level](https://docs.pydantic.dev/latest/concepts/json_schema/#field-level-customization) or at the [Model level](https://docs.pydantic.dev/latest/concepts/json_schema/#model-level-customization). You can pass a `dict` or a `Callable` to `json_schema_extra`.

You can pass a `dict` to `json_schema_extra` to add extra information to the JSON schema:

```python
import json

from pydantic import BaseModel, ConfigDict

class Model(BaseModel):
    a: str

    model_config = ConfigDict(json_schema_extra={'examples': [{'a': 'Foo'}]})

print(json.dumps(Model.model_json_schema(), indent=2))
```

JSON output:

```json
{
  "examples": [
    {
      "a": "Foo"
    }
  ],
  "properties": {
    "a": {
      "title": "A",
      "type": "string"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
```

You can pass a `Callable` to `json_schema_extra` to modify the JSON schema with a function:

```python
import json

from pydantic import BaseModel, Field

def pop_default(s):
    s.pop('default')

class Model(BaseModel):
    a: int = Field(default=1, json_schema_extra=pop_default)

print(json.dumps(Model.model_json_schema(), indent=2))
```

JSON output:

```json
{
  "properties": {
    "a": {
      "title": "A",
      "type": "integer"
    }
  },
  "title": "Model",
  "type": "object"
}
```

Starting in v2.9, Pydantic merges `json_schema_extra` dictionaries from annotated types. This pattern offers a more additive approach to merging rather than the previous override behavior. This can be quite helpful for cases of reusing json schema extra information across multiple types.

We viewed this change largely as a bug fix, as it resolves unintentional differences in the `json_schema_extra` merging behavior between `BaseModel` and `TypeAdapter` instances - see [this issue](https://github.com/pydantic/pydantic/issues/9210) for more details.

```
import json
from typing import Annotated

from typing_extensions import TypeAlias

from pydantic import Field, TypeAdapter

ExternalType: TypeAlias = Annotated[
    int, Field(json_schema_extra={'key1': 'value1'})
]

ta = TypeAdapter(
    Annotated[ExternalType, Field(json_schema_extra={'key2': 'value2'})]
)
print(json.dumps(ta.json_schema(), indent=2))
"""
{
  "key1": "value1",
  "key2": "value2",
  "type": "integer"
}
"""
```

```
import json
from typing import Annotated

from typing import TypeAlias

from pydantic import Field, TypeAdapter

ExternalType: TypeAlias = Annotated[
    int, Field(json_schema_extra={'key1': 'value1'})
]

ta = TypeAdapter(
    Annotated[ExternalType, Field(json_schema_extra={'key2': 'value2'})]
)
print(json.dumps(ta.json_schema(), indent=2))
"""
{
  "key1": "value1",
  "key2": "value2",
  "type": "integer"
}
"""
```

Note

We no longer (and never fully did) support composing a mix of `dict` and `callable` type `json_schema_extra` specifications. If this is a requirement for your use case, please [open a pydantic issue](https://github.com/pydantic/pydantic/issues/new/choose) and explain your situation - we'd be happy to reconsider this decision when presented with a compelling case.

### `WithJsonSchema` annotation[¶](https://docs.pydantic.dev/latest/concepts/json_schema/#withjsonschema-annotation "Permanent link")

API Documentation

[`pydantic.json_schema.WithJsonSchema`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema.WithJsonSchema)  

The [`WithJsonSchema`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema.WithJsonSchema) annotation can be used to override the generated (base) JSON schema for a given type without the need to implement `__get_pydantic_core_schema__` or `__get_pydantic_json_schema__` on the type itself. Note that this overrides the whole JSON Schema generation process for the field (in the following example, the `'type'` also needs to be provided).

```python
import json
from typing import Annotated

from pydantic import BaseModel, WithJsonSchema

MyInt = Annotated[
    int,
    WithJsonSchema({'type': 'integer', 'examples': [1, 0, -1]}),
]

class Model(BaseModel):
    a: MyInt

print(json.dumps(Model.model_json_schema(), indent=2))
```

JSON output:

```json
{
  "properties": {
    "a": {
      "examples": [
        1,
        0,
        -1
      ],
      "title": "A",
      "type": "integer"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
```

### `SkipJsonSchema` annotation[¶](https://docs.pydantic.dev/latest/concepts/json_schema/#skipjsonschema-annotation "Permanent link")

API Documentation

[`pydantic.json_schema.SkipJsonSchema`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema.SkipJsonSchema)  

The [`SkipJsonSchema`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema.SkipJsonSchema) annotation can be used to skip an included field (or part of a field's specifications) from the generated JSON schema. See the API docs for more details.

### Implementing `__get_pydantic_core_schema__` [¶](https://docs.pydantic.dev/latest/concepts/json_schema/#implementing-__get_pydantic_core_schema__ "Permanent link")

Custom types (used as `field_name: TheType` or `field_name: Annotated[TheType, ...]`) as well as `Annotated` metadata (used as `field_name: Annotated[int, SomeMetadata]`) can modify or override the generated schema by implementing `__get_pydantic_core_schema__`. This method receives two positional arguments:

1. The type annotation that corresponds to this type (so in the case of `TheType[T][int]` it would be `TheType[int]`).
2. A handler/callback to call the next implementer of `__get_pydantic_core_schema__`.

The handler system works just like [*wrap* field validators](https://docs.pydantic.dev/latest/concepts/validators/#field-wrap-validator). In this case the input is the type and the output is a `core_schema`.

Here is an example of a custom type that *overrides* the generated `core_schema`:

```python
from dataclasses import dataclass
from typing import Any

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler

@dataclass
class CompressedString:
    dictionary: dict[int, str]
    text: list[int]

    def build(self) -> str:
        return ' '.join([self.dictionary[key] for key in self.text])

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        assert source is CompressedString
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
                return_schema=core_schema.str_schema(),
            ),
        )

    @staticmethod
    def _validate(value: str) -> 'CompressedString':
        inverse_dictionary: dict[str, int] = {}
        text: list[int] = []
        for word in value.split(' '):
            if word not in inverse_dictionary:
                inverse_dictionary[word] = len(inverse_dictionary)
            text.append(inverse_dictionary[word])
        return CompressedString(
            {v: k for k, v in inverse_dictionary.items()}, text
        )

    @staticmethod
    def _serialize(value: 'CompressedString') -> str:
        return value.build()

class MyModel(BaseModel):
    value: CompressedString

print(MyModel.model_json_schema())
"""
{
    'properties': {'value': {'title': 'Value', 'type': 'string'}},
    'required': ['value'],
    'title': 'MyModel',
    'type': 'object',
}
"""
print(MyModel(value='fox fox fox dog fox'))
"""
value = CompressedString(dictionary={0: 'fox', 1: 'dog'}, text=[0, 0, 0, 1, 0])
"""

print(MyModel(value='fox fox fox dog fox').model_dump(mode='json'))
#> {'value': 'fox fox fox dog fox'}
```

Since Pydantic would not know how to generate a schema for `CompressedString`, if you call `handler(source)` in its `__get_pydantic_core_schema__` method you would get a `pydantic.errors.PydanticSchemaGenerationError` error. This will be the case for most custom types, so you almost never want to call into `handler` for custom types.

The process for `Annotated` metadata is much the same except that you can generally call into `handler` to have Pydantic handle generating the schema.

```
from dataclasses import dataclass
from typing import Annotated, Any, Sequence

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationError

@dataclass
class RestrictCharacters:
    alphabet: Sequence[str]

    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        if not self.alphabet:
            raise ValueError('Alphabet may not be empty')
        schema = handler(
            source
        )  # get the CoreSchema from the type / inner constraints
        if schema['type'] != 'str':
            raise TypeError('RestrictCharacters can only be applied to strings')
        return core_schema.no_info_after_validator_function(
            self.validate,
            schema,
        )

    def validate(self, value: str) -> str:
        if any(c not in self.alphabet for c in value):
            raise ValueError(
                f'{value!r} is not restricted to {self.alphabet!r}'
            )
        return value

class MyModel(BaseModel):
    value: Annotated[str, RestrictCharacters('ABC')]

print(MyModel.model_json_schema())
"""
{
    'properties': {'value': {'title': 'Value', 'type': 'string'}},
    'required': ['value'],
    'title': 'MyModel',
    'type': 'object',
}
"""
print(MyModel(value='CBA'))
#> value='CBA'

try:
    MyModel(value='XYZ')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    value
      Value error, 'XYZ' is not restricted to 'ABC' [type=value_error, input_value='XYZ', input_type=str]
    """
```

```
from dataclasses import dataclass
from typing import Annotated, Any
from collections.abc import Sequence

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationError

@dataclass
class RestrictCharacters:
    alphabet: Sequence[str]

    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        if not self.alphabet:
            raise ValueError('Alphabet may not be empty')
        schema = handler(
            source
        )  # get the CoreSchema from the type / inner constraints
        if schema['type'] != 'str':
            raise TypeError('RestrictCharacters can only be applied to strings')
        return core_schema.no_info_after_validator_function(
            self.validate,
            schema,
        )

    def validate(self, value: str) -> str:
        if any(c not in self.alphabet for c in value):
            raise ValueError(
                f'{value!r} is not restricted to {self.alphabet!r}'
            )
        return value

class MyModel(BaseModel):
    value: Annotated[str, RestrictCharacters('ABC')]

print(MyModel.model_json_schema())
"""
{
    'properties': {'value': {'title': 'Value', 'type': 'string'}},
    'required': ['value'],
    'title': 'MyModel',
    'type': 'object',
}
"""
print(MyModel(value='CBA'))
#> value='CBA'

try:
    MyModel(value='XYZ')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    value
      Value error, 'XYZ' is not restricted to 'ABC' [type=value_error, input_value='XYZ', input_type=str]
    """
```

So far we have been wrapping the schema, but if you just want to *modify* it or *ignore* it you can as well.

To modify the schema, first call the handler, then mutate the result:

```python
from typing import Annotated, Any

from pydantic_core import ValidationError, core_schema

from pydantic import BaseModel, GetCoreSchemaHandler

class SmallString:
    def __get_pydantic_core_schema__(
        self,
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = handler(source)
        assert schema['type'] == 'str'
        schema['max_length'] = 10  # modify in place
        return schema

class MyModel(BaseModel):
    value: Annotated[str, SmallString()]

try:
    MyModel(value='too long!!!!!')
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    value
      String should have at most 10 characters [type=string_too_long, input_value='too long!!!!!', input_type=str]
    """
```

Tip

Note that you *must* return a schema, even if you are just mutating it in place.

To override the schema completely, do not call the handler and return your own `CoreSchema`:

```python
from typing import Annotated, Any

from pydantic_core import ValidationError, core_schema

from pydantic import BaseModel, GetCoreSchemaHandler

class AllowAnySubclass:
    def __get_pydantic_core_schema__(
        self, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # we can't call handler since it will fail for arbitrary types
        def validate(value: Any) -> Any:
            if not isinstance(value, source):
                raise ValueError(
                    f'Expected an instance of {source}, got an instance of {type(value)}'
                )

        return core_schema.no_info_plain_validator_function(validate)

class Foo:
    pass

class Model(BaseModel):
    f: Annotated[Foo, AllowAnySubclass()]

print(Model(f=Foo()))
#> f=None

class NotFoo:
    pass

try:
    Model(f=NotFoo())
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    f
      Value error, Expected an instance of <class '__main__.Foo'>, got an instance of <class '__main__.NotFoo'> [type=value_error, input_value=<__main__.NotFoo object at 0x0123456789ab>, input_type=NotFoo]
    """
```

### Implementing `__get_pydantic_json_schema__` [¶](https://docs.pydantic.dev/latest/concepts/json_schema/#implementing-__get_pydantic_json_schema__ "Permanent link")

You can also implement `__get_pydantic_json_schema__` to modify or override the generated json schema. Modifying this method only affects the JSON schema - it doesn't affect the core schema, which is used for validation and serialization.

Here's an example of modifying the generated JSON schema:

```python
import json
from typing import Any

from pydantic_core import core_schema as cs

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler, TypeAdapter
from pydantic.json_schema import JsonSchemaValue

class Person:
    name: str
    age: int

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> cs.CoreSchema:
        return cs.typed_dict_schema(
            {
                'name': cs.typed_dict_field(cs.str_schema()),
                'age': cs.typed_dict_field(cs.int_schema()),
            },
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema['examples'] = [
            {
                'name': 'John Doe',
                'age': 25,
            }
        ]
        json_schema['title'] = 'Person'
        return json_schema

print(json.dumps(TypeAdapter(Person).json_schema(), indent=2))
```

JSON output:

```json
{
  "examples": [
    {
      "age": 25,
      "name": "John Doe"
    }
  ],
  "properties": {
    "name": {
      "title": "Name",
      "type": "string"
    },
    "age": {
      "title": "Age",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Person",
  "type": "object"
}
```

### Using `field_title_generator`[¶](https://docs.pydantic.dev/latest/concepts/json_schema/#using-field_title_generator "Permanent link")

The `field_title_generator` parameter can be used to programmatically generate the title for a field based on its name and info. This is similar to the field level `field_title_generator`, but the `ConfigDict` option will be applied to all fields of the class.

See the following example:

```python
import json

from pydantic import BaseModel, ConfigDict

class Person(BaseModel):
    model_config = ConfigDict(
        field_title_generator=lambda field_name, field_info: field_name.upper()
    )
    name: str
    age: int

print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "properties": {
    "name": {
      "title": "NAME",
      "type": "string"
    },
    "age": {
      "title": "AGE",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Person",
  "type": "object"
}
"""
```

### Using `model_title_generator`[¶](https://docs.pydantic.dev/latest/concepts/json_schema/#using-model_title_generator "Permanent link")

The `model_title_generator` config option is similar to the `field_title_generator` option, but it applies to the title of the model itself, and accepts the model class as input.

See the following example:

```python
import json

from pydantic import BaseModel, ConfigDict

def make_title(model: type) -> str:
    return f'Title-{model.__name__}'

class Person(BaseModel):
    model_config = ConfigDict(model_title_generator=make_title)
    name: str
    age: int

print(json.dumps(Person.model_json_schema(), indent=2))
"""
{
  "properties": {
    "name": {
      "title": "Name",
      "type": "string"
    },
    "age": {
      "title": "Age",
      "type": "integer"
    }
  },
  "required": [
    "name",
    "age"
  ],
  "title": "Title-Person",
  "type": "object"
}
"""
```

## JSON schema types¶

Types, custom field types, and constraints (like `max_length`) are mapped to the corresponding spec formats in the following priority order (when there is an equivalent available):

1. [JSON Schema Core](https://json-schema.org/draft/2020-12/json-schema-core)
2. [JSON Schema Validation](https://json-schema.org/draft/2020-12/json-schema-validation)
3. [OpenAPI Data Types](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types)
4. The standard `format` JSON field is used to define Pydantic extensions for more complex `string` sub-types.

The field schema mapping from Python or Pydantic to JSON schema is done as follows:

{{ schema\_mappings\_table }}

## Top-level schema generation¶

You can also generate a top-level JSON schema that only includes a list of models and related sub-models in its `$defs`:

```python
import json

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

class Foo(BaseModel):
    a: str = None

class Model(BaseModel):
    b: Foo

class Bar(BaseModel):
    c: int

_, top_level_schema = models_json_schema(
    [(Model, 'validation'), (Bar, 'validation')], title='My Schema'
)
print(json.dumps(top_level_schema, indent=2))
```

JSON output:

```json
{
  "$defs": {
    "Bar": {
      "properties": {
        "c": {
          "title": "C",
          "type": "integer"
        }
      },
      "required": [
        "c"
      ],
      "title": "Bar",
      "type": "object"
    },
    "Foo": {
      "properties": {
        "a": {
          "default": null,
          "title": "A",
          "type": "string"
        }
      },
      "title": "Foo",
      "type": "object"
    },
    "Model": {
      "properties": {
        "b": {
          "$ref": "#/$defs/Foo"
        }
      },
      "required": [
        "b"
      ],
      "title": "Model",
      "type": "object"
    }
  },
  "title": "My Schema"
}
```

## Customizing the JSON Schema Generation Process¶
API Documentation

[`pydantic.json_schema`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema.GenerateJsonSchema)  

If you need custom schema generation, you can use a `schema_generator`, modifying the [`GenerateJsonSchema`](https://docs.pydantic.dev/latest/api/json_schema/#pydantic.json_schema.GenerateJsonSchema) class as necessary for your application.

The various methods that can be used to produce JSON schema accept a keyword argument `schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema`, and you can pass your custom subclass to these methods in order to use your own approach to generating JSON schema.

`GenerateJsonSchema` implements the translation of a type's `pydantic-core` schema into a JSON schema. By design, this class breaks the JSON schema generation process into smaller methods that can be easily overridden in subclasses to modify the "global" approach to generating JSON schema.

```python
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema

class MyGenerateJsonSchema(GenerateJsonSchema):
    def generate(self, schema, mode='validation'):
        json_schema = super().generate(schema, mode=mode)
        json_schema['title'] = 'Customize title'
        json_schema['$schema'] = self.schema_dialect
        return json_schema

class MyModel(BaseModel):
    x: int

print(MyModel.model_json_schema(schema_generator=MyGenerateJsonSchema))
"""
{
    'properties': {'x': {'title': 'X', 'type': 'integer'}},
    'required': ['x'],
    'title': 'Customize title',
    'type': 'object',
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
}
"""
```

Below is an approach you can use to exclude any fields from the schema that don't have valid json schemas:

```
from typing import Callable

from pydantic_core import PydanticOmit, core_schema

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

class MyGenerateJsonSchema(GenerateJsonSchema):
    def handle_invalid_for_json_schema(
        self, schema: core_schema.CoreSchema, error_info: str
    ) -> JsonSchemaValue:
        raise PydanticOmit

def example_callable():
    return 1

class Example(BaseModel):
    name: str = 'example'
    function: Callable = example_callable

instance_example = Example()

validation_schema = instance_example.model_json_schema(
    schema_generator=MyGenerateJsonSchema, mode='validation'
)
print(validation_schema)
"""
{
    'properties': {
        'name': {'default': 'example', 'title': 'Name', 'type': 'string'}
    },
    'title': 'Example',
    'type': 'object',
}
"""
```

```
from collections.abc import Callable

from pydantic_core import PydanticOmit, core_schema

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

class MyGenerateJsonSchema(GenerateJsonSchema):
    def handle_invalid_for_json_schema(
        self, schema: core_schema.CoreSchema, error_info: str
    ) -> JsonSchemaValue:
        raise PydanticOmit

def example_callable():
    return 1

class Example(BaseModel):
    name: str = 'example'
    function: Callable = example_callable

instance_example = Example()

validation_schema = instance_example.model_json_schema(
    schema_generator=MyGenerateJsonSchema, mode='validation'
)
print(validation_schema)
"""
{
    'properties': {
        'name': {'default': 'example', 'title': 'Name', 'type': 'string'}
    },
    'title': 'Example',
    'type': 'object',
}
"""
```

### JSON schema sorting¶

By default, Pydantic recursively sorts JSON schemas by alphabetically sorting keys. Notably, Pydantic skips sorting the values of the `properties` key, to preserve the order of the fields as they were defined in the model.

If you would like to customize this behavior, you can override the `sort` method in your custom `GenerateJsonSchema` subclass. The below example uses a no-op `sort` method to disable sorting entirely, which is reflected in the preserved order of the model fields and `json_schema_extra` keys:

```
import json
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

class MyGenerateJsonSchema(GenerateJsonSchema):
    def sort(
        self, value: JsonSchemaValue, parent_key: Optional[str] = None
    ) -> JsonSchemaValue:
        """No-op, we don't want to sort schema values at all."""
        return value

class Bar(BaseModel):
    c: str
    b: str
    a: str = Field(json_schema_extra={'c': 'hi', 'b': 'hello', 'a': 'world'})

json_schema = Bar.model_json_schema(schema_generator=MyGenerateJsonSchema)
print(json.dumps(json_schema, indent=2))
"""
{
  "type": "object",
  "properties": {
    "c": {
      "type": "string",
      "title": "C"
    },
    "b": {
      "type": "string",
      "title": "B"
    },
    "a": {
      "type": "string",
      "c": "hi",
      "b": "hello",
      "a": "world",
      "title": "A"
    }
  },
  "required": [
    "c",
    "b",
    "a"
  ],
  "title": "Bar"
}
"""
```

```
import json

from pydantic import BaseModel, Field
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

class MyGenerateJsonSchema(GenerateJsonSchema):
    def sort(
        self, value: JsonSchemaValue, parent_key: str | None = None
    ) -> JsonSchemaValue:
        """No-op, we don't want to sort schema values at all."""
        return value

class Bar(BaseModel):
    c: str
    b: str
    a: str = Field(json_schema_extra={'c': 'hi', 'b': 'hello', 'a': 'world'})

json_schema = Bar.model_json_schema(schema_generator=MyGenerateJsonSchema)
print(json.dumps(json_schema, indent=2))
"""
{
  "type": "object",
  "properties": {
    "c": {
      "type": "string",
      "title": "C"
    },
    "b": {
      "type": "string",
      "title": "B"
    },
    "a": {
      "type": "string",
      "c": "hi",
      "b": "hello",
      "a": "world",
      "title": "A"
    }
  },
  "required": [
    "c",
    "b",
    "a"
  ],
  "title": "Bar"
}
"""
```

## Customizing the `$ref`s in JSON Schema[¶](https://docs.pydantic.dev/latest/concepts/json_schema/#customizing-the-refs-in-json-schema "Permanent link")

The format of `$ref`s can be altered by calling [`model_json_schema()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_json_schema) or [`model_dump_json()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json) with the `ref_template` keyword argument. The definitions are always stored under the key `$defs`, but a specified prefix can be used for the references.

This is useful if you need to extend or modify the JSON schema default definitions location. For example, with OpenAPI:

```python
import json

from pydantic import BaseModel
from pydantic.type_adapter import TypeAdapter

class Foo(BaseModel):
    a: int

class Model(BaseModel):
    a: Foo

adapter = TypeAdapter(Model)

print(
    json.dumps(
        adapter.json_schema(ref_template='#/components/schemas/{model}'),
        indent=2,
    )
)
```

JSON output:

```json
{
  "$defs": {
    "Foo": {
      "properties": {
        "a": {
          "title": "A",
          "type": "integer"
        }
      },
      "required": [
        "a"
      ],
      "title": "Foo",
      "type": "object"
    }
  },
  "properties": {
    "a": {
      "$ref": "#/components/schemas/Foo"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
```

## Miscellaneous Notes on JSON Schema Generation¶

- The JSON schema for `Optional` fields indicates that the value `null` is allowed.
- The `Decimal` type is exposed in JSON schema (and serialized) as a string.
- Since the `namedtuple` type doesn't exist in JSON, a model's JSON schema does not preserve `namedtuple`s as `namedtuple`s.
- Sub-models used are added to the `$defs` JSON attribute and referenced, as per the spec.
- Sub-models with modifications (via the `Field` class) like a custom title, description, or default value, are recursively included instead of referenced.
- The `description` for models is taken from either the docstring of the class or the argument `description` to the `Field` class.
- The schema is generated by default using aliases as keys, but it can be generated using model property names instead by calling [`model_json_schema()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_json_schema) or [`model_dump_json()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json) with the `by_alias=False` keyword argument.

---
title: "JSON - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/json/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
## Json Parsing¶
API Documentation

[`pydantic.main.BaseModel.model_validate_json`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_json) [`pydantic.type_adapter.TypeAdapter.validate_json`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter.validate_json) [`pydantic_core.from_json`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.from_json)

Pydantic provides builtin JSON parsing, which helps achieve:

- Significant performance improvements without the cost of using a 3rd party library
- Support for custom errors
- Support for `strict` specifications

Here's an example of Pydantic's builtin JSON parsing via the [`model_validate_json`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_json) method, showcasing the support for `strict` specifications while parsing JSON data that doesn't match the model's type annotations:

```python
from datetime import date

from pydantic import BaseModel, ConfigDict, ValidationError

class Event(BaseModel):
    model_config = ConfigDict(strict=True)

    when: date
    where: tuple[int, int]

json_data = '{"when": "1987-01-28", "where": [51, -1]}'
print(Event.model_validate_json(json_data))  
#> when=datetime.date(1987, 1, 28) where=(51, -1)

try:
    Event.model_validate({'when': '1987-01-28', 'where': [51, -1]})  
except ValidationError as e:
    print(e)
    """
    2 validation errors for Event
    when
      Input should be a valid date [type=date_type, input_value='1987-01-28', input_type=str]
    where
      Input should be a valid tuple [type=tuple_type, input_value=[51, -1], input_type=list]
    """
```

In v2.5.0 and above, Pydantic uses [`jiter`](https://docs.rs/jiter/latest/jiter/), a fast and iterable JSON parser, to parse JSON data. Using `jiter` compared to `serde` results in modest performance improvements that will get even better in the future.

The `jiter` JSON parser is almost entirely compatible with the `serde` JSON parser, with one noticeable enhancement being that `jiter` supports deserialization of `inf` and `NaN` values. In the future, `jiter` is intended to enable support validation errors to include the location in the original JSON input which contained the invalid value.

### Partial JSON Parsing¶

**Starting in v2.7.0**, Pydantic's [JSON parser](https://docs.rs/jiter/latest/jiter/) offers support for partial JSON parsing, which is exposed via [`pydantic_core.from_json`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.from_json). Here's an example of this feature in action:

```python
from pydantic_core import from_json

partial_json_data = '["aa", "bb", "c'  

try:
    result = from_json(partial_json_data, allow_partial=False)
except ValueError as e:
    print(e)  
    #> EOF while parsing a string at line 1 column 15

result = from_json(partial_json_data, allow_partial=True)
print(result)  
#> ['aa', 'bb']
```

This also works for deserializing partial dictionaries. For example:

```python
from pydantic_core import from_json

partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog_dict = from_json(partial_dog_json, allow_partial=True)
print(dog_dict)
#> {'breed': 'lab', 'name': 'fluffy', 'friends': ['buddy', 'spot', 'rufus']}
```

Validating LLM Output

This feature is particularly beneficial for validating LLM outputs. We've written some blog posts about this topic, which you can find [here](https://pydantic.dev/articles).

In future versions of Pydantic, we expect to expand support for this feature through either Pydantic's other JSON validation functions ([`pydantic.main.BaseModel.model_validate_json`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_json) and [`pydantic.type_adapter.TypeAdapter.validate_json`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter.validate_json)) or model configuration. Stay tuned 🚀!

For now, you can use [`pydantic_core.from_json`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.from_json) in combination with [`pydantic.main.BaseModel.model_validate`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate) to achieve the same result. Here's an example:

```python
from pydantic_core import from_json

from pydantic import BaseModel

class Dog(BaseModel):
    breed: str
    name: str
    friends: list

partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog = Dog.model_validate(from_json(partial_dog_json, allow_partial=True))
print(repr(dog))
#> Dog(breed='lab', name='fluffy', friends=['buddy', 'spot', 'rufus'])
```

Tip

For partial JSON parsing to work reliably, all fields on the model should have default values.

Check out the following example for a more in-depth look at how to use default values with partial JSON parsing:

Using default values with partial JSON parsing

```python
from typing import Annotated, Any, Optional

import pydantic_core

from pydantic import BaseModel, ValidationError, WrapValidator

def default_on_error(v, handler) -> Any:
    """
    Raise a PydanticUseDefault exception if the value is missing.

    This is useful for avoiding errors from partial
    JSON preventing successful validation.
    """
    try:
        return handler(v)
    except ValidationError as exc:
        # there might be other types of errors resulting from partial JSON parsing
        # that you allow here, feel free to customize as needed
        if all(e['type'] == 'missing' for e in exc.errors()):
            raise pydantic_core.PydanticUseDefault()
        else:
            raise

class NestedModel(BaseModel):
    x: int
    y: str

class MyModel(BaseModel):
    foo: Optional[str] = None
    bar: Annotated[
        Optional[tuple[str, int]], WrapValidator(default_on_error)
    ] = None
    nested: Annotated[
        Optional[NestedModel], WrapValidator(default_on_error)
    ] = None

m = MyModel.model_validate(
    pydantic_core.from_json('{"foo": "x", "bar": ["world",', allow_partial=True)
)
print(repr(m))
#> MyModel(foo='x', bar=None, nested=None)

m = MyModel.model_validate(
    pydantic_core.from_json(
        '{"foo": "x", "bar": ["world", 1], "nested": {"x":', allow_partial=True
    )
)
print(repr(m))
#> MyModel(foo='x', bar=('world', 1), nested=None)
```

### Caching Strings¶

**Starting in v2.7.0**, Pydantic's [JSON parser](https://docs.rs/jiter/latest/jiter/) offers support for configuring how Python strings are cached during JSON parsing and validation (when Python strings are constructed from Rust strings during Python validation, e.g. after `strip_whitespace=True`). The `cache_strings` setting is exposed via both [model config](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict) and [`pydantic_core.from_json`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.from_json).

The `cache_strings` setting can take any of the following values:

- `True` or `'all'` (the default): cache all strings
- `'keys'`: cache only dictionary keys, this **only** applies when used with [`pydantic_core.from_json`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.from_json) or when parsing JSON using [`Json`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.Json)
- `False` or `'none'`: no caching

Using the string caching feature results in performance improvements, but increases memory usage slightly.

String Caching Details

1. Strings are cached using a fully associative cache with a size of [16,384](https://github.com/pydantic/jiter/blob/5bbdcfd22882b7b286416b22f74abd549c7b2fd7/src/py_string_cache.rs#L113).
2. Only strings where `len(string) < 64` are cached.
3. There is some overhead to looking up the cache, which is normally worth it to avoid constructing strings. However, if you know there will be very few repeated strings in your data, you might get a performance boost by disabling this setting with `cache_strings=False`.

## JSON Serialization¶
API Documentation

[`pydantic.main.BaseModel.model_dump_json`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json)  
[`pydantic.type_adapter.TypeAdapter.dump_json`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter.dump_json)  
[`pydantic_core.to_json`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.to_json)  

For more information on JSON serialization, see the [Serialization Concepts](https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump_json) page.

---
title: "Types - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/types/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
Where possible Pydantic uses [standard library types](https://docs.pydantic.dev/latest/api/standard_library_types/) to define fields, thus smoothing the learning curve. For many useful applications, however, no standard library type exists, so Pydantic implements many commonly used types.

There are also more complex types that can be found in the [Pydantic Extra Types](https://github.com/pydantic/pydantic-extra-types) package.

If no existing type suits your purpose you can also implement your [own Pydantic-compatible types](https://docs.pydantic.dev/latest/concepts/types/#custom-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.

- [Standard Library Types](https://docs.pydantic.dev/latest/api/standard_library_types/) — types from the Python standard library.
- [Strict Types](https://docs.pydantic.dev/latest/concepts/types/#strict-types) — types that enable you to prevent coercion from compatible types.
- [Custom Data Types](https://docs.pydantic.dev/latest/concepts/types/#custom-types) — create your own custom data types.
- [Field Type Conversions](https://docs.pydantic.dev/latest/concepts/conversion_table/) — strict and lax conversion between different field types.

## Type conversion¶

During validation, Pydantic can coerce data into expected types.

There are two modes of coercion: strict and lax. See [Conversion Table](https://docs.pydantic.dev/latest/concepts/conversion_table/) for more details on how Pydantic converts data in both strict and lax modes.

See [Strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) and [Strict Types](https://docs.pydantic.dev/latest/concepts/types/#strict-types) for details on enabling strict coercion.

## Strict Types¶

Pydantic provides the following strict types:

- [`StrictBool`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StrictBool)
- [`StrictBytes`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StrictBytes)
- [`StrictFloat`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StrictFloat)
- [`StrictInt`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StrictInt)
- [`StrictStr`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StrictStr)

These types will only pass validation when the validated value is of the respective type or is a subtype of that type.

### Constrained types¶

This behavior is also exposed via the `strict` field of the constrained types and can be combined with a multitude of complex validation rules. See the individual type signatures for supported arguments.

- [`conbytes()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.conbytes)
- [`condate()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.condate)
- [`condecimal()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.condecimal)
- [`confloat()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.confloat)
- [`confrozenset()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.confrozenset)
- [`conint()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.conint)
- [`conlist()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.conlist)
- [`conset()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.conset)
- [`constr()`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.constr)

The following caveats apply:

- `StrictBytes` (and the `strict` option of `conbytes()`) will accept both `bytes`, and `bytearray` types.
- `StrictInt` (and the `strict` option of `conint()`) will not accept `bool` types, even though `bool` is a subclass of `int` in Python. Other subclasses will work.
- `StrictFloat` (and the `strict` option of `confloat()`) will not accept `int`.

Besides the above, you can also have a [`FiniteFloat`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.FiniteFloat) type that will only accept finite values (i.e. not `inf`, `-inf` or `nan`).

## Custom Types¶

You can also define your own custom data types. There are several ways to achieve it.

### Using the annotated pattern¶

The [annotated pattern](https://docs.pydantic.dev/latest/concepts/fields/#the-annotated-pattern) can be used to make types reusable across your code base. For example, to create a type representing a positive integer:

```python
from typing import Annotated

from pydantic import Field, TypeAdapter, ValidationError

PositiveInt = Annotated[int, Field(gt=0)]  

ta = TypeAdapter(PositiveInt)

print(ta.validate_python(1))
#> 1

try:
    ta.validate_python(-1)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for constrained-int
      Input should be greater than 0 [type=greater_than, input_value=-1, input_type=int]
    """
```

#### Adding validation and serialization¶

You can add or override validation, serialization, and JSON schemas to an arbitrary type using the markers that Pydantic exports:

```python
from typing import Annotated

from pydantic import (
    AfterValidator,
    PlainSerializer,
    TypeAdapter,
    WithJsonSchema,
)

TruncatedFloat = Annotated[
    float,
    AfterValidator(lambda x: round(x, 1)),
    PlainSerializer(lambda x: f'{x:.1e}', return_type=str),
    WithJsonSchema({'type': 'string'}, mode='serialization'),
]

ta = TypeAdapter(TruncatedFloat)

input = 1.02345
assert input != 1.0

assert ta.validate_python(input) == 1.0

assert ta.dump_json(input) == b'"1.0e+00"'

assert ta.json_schema(mode='validation') == {'type': 'number'}
assert ta.json_schema(mode='serialization') == {'type': 'string'}
```

#### Generics¶

[Type variables](https://docs.python.org/3/library/typing.html#typing.TypeVar) can be used within the [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) type:

```python
from typing import Annotated, TypeVar

from annotated_types import Gt, Len

from pydantic import TypeAdapter, ValidationError

T = TypeVar('T')

ShortList = Annotated[list[T], Len(max_length=4)]

ta = TypeAdapter(ShortList[int])

v = ta.validate_python([1, 2, 3, 4])
assert v == [1, 2, 3, 4]

try:
    ta.validate_python([1, 2, 3, 4, 5])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[int]
      List should have at most 4 items after validation, not 5 [type=too_long, input_value=[1, 2, 3, 4, 5], input_type=list]
    """

PositiveList = list[Annotated[T, Gt(0)]]

ta = TypeAdapter(PositiveList[float])

v = ta.validate_python([1.0])
assert type(v[0]) is float

try:
    ta.validate_python([-1.0])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[constrained-float]
    0
      Input should be greater than 0 [type=greater_than, input_value=-1.0, input_type=float]
    """
```

### Named type aliases¶

The above examples make use of *implicit* type aliases, assigned to a variable. At runtime, Pydantic has no way of knowing the name of the variable it was assigned to, and this can be problematic for two reasons:

- The [JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/) of the alias won't be converted into a [definition](https://json-schema.org/understanding-json-schema/structuring#defs). This is mostly useful when you are using the alias more than once in a model definition.
- In most cases, [recursive type aliases](https://docs.pydantic.dev/latest/concepts/types/#named-recursive-types) won't work.

By leveraging the new [`type` statement](https://typing.readthedocs.io/en/latest/spec/aliases.html#type-statement) (introduced in [PEP 695](https://peps.python.org/pep-0695/)), you can define aliases as follows:

```
from typing import Annotated

from annotated_types import Gt
from typing_extensions import TypeAliasType

from pydantic import BaseModel

PositiveIntList = TypeAliasType('PositiveIntList', list[Annotated[int, Gt(0)]])

class Model(BaseModel):
    x: PositiveIntList
    y: PositiveIntList

print(Model.model_json_schema())  
"""
{
    '$defs': {
        'PositiveIntList': {
            'items': {'exclusiveMinimum': 0, 'type': 'integer'},
            'type': 'array',
        }
    },
    'properties': {
        'x': {'$ref': '#/$defs/PositiveIntList'},
        'y': {'$ref': '#/$defs/PositiveIntList'},
    },
    'required': ['x', 'y'],
    'title': 'Model',
    'type': 'object',
}
"""
```

```python
from typing import Annotated

from annotated_types import Gt

from pydantic import BaseModel

type PositiveIntList = list[Annotated[int, Gt(0)]]

class Model(BaseModel):
    x: PositiveIntList
    y: PositiveIntList

print(Model.model_json_schema())  
"""
{
    '$defs': {
        'PositiveIntList': {
            'items': {'exclusiveMinimum': 0, 'type': 'integer'},
            'type': 'array',
        }
    },
    'properties': {
        'x': {'$ref': '#/$defs/PositiveIntList'},
        'y': {'$ref': '#/$defs/PositiveIntList'},
    },
    'required': ['x', 'y'],
    'title': 'Model',
    'type': 'object',
}
"""
```

1. If `PositiveIntList` were to be defined as an implicit type alias, its definition would have been duplicated in both `'x'` and `'y'`.

When to use named type aliases

While (named) PEP 695 and implicit type aliases are meant to be equivalent for static type checkers, Pydantic will *not* understand field-specific metadata inside named aliases. That is, metadata such as `alias`, `default`, `deprecated`, *cannot* be used:

```
from typing import Annotated

from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field

MyAlias = TypeAliasType('MyAlias', Annotated[int, Field(default=1)])

class Model(BaseModel):
    x: MyAlias  # This is not allowed
```

```
from typing import Annotated

from pydantic import BaseModel, Field

type MyAlias = Annotated[int, Field(default=1)]

class Model(BaseModel):
    x: MyAlias  # This is not allowed
```

Only metadata that can be applied to the annotated type itself is allowed (e.g. [validation constraints](https://docs.pydantic.dev/latest/concepts/fields/#field-constraints) and JSON metadata). Trying to support field-specific metadata would require eagerly inspecting the type alias's [`__value__`](https://docs.python.org/3/library/typing.html#typing.TypeAliasType.__value__), and as such Pydantic wouldn't be able to have the alias stored as a JSON Schema definition.

Note

As with implicit type aliases, [type variables](https://docs.python.org/3/library/typing.html#typing.TypeVar) can also be used inside the generic alias:

```
from typing import Annotated, TypeVar

from annotated_types import Len
from typing_extensions import TypeAliasType

T = TypeVar('T')

ShortList = TypeAliasType(
    'ShortList', Annotated[list[T], Len(max_length=4)], type_params=(T,)
)
```

```
from typing import Annotated, TypeVar

from annotated_types import Len

type ShortList[T] = Annotated[list[T], Len(max_length=4)]
```

#### Named recursive types¶

Named type aliases should be used whenever you need to define recursive type aliases

.

For instance, here is an example definition of a JSON type:

```
from typing import Union

from typing_extensions import TypeAliasType

from pydantic import TypeAdapter

Json = TypeAliasType(
    'Json',
    'Union[dict[str, Json], list[Json], str, int, float, bool, None]',  
)

ta = TypeAdapter(Json)
print(ta.json_schema())
"""
{
    '$defs': {
        'Json': {
            'anyOf': [
                {
                    'additionalProperties': {'$ref': '#/$defs/Json'},
                    'type': 'object',
                },
                {'items': {'$ref': '#/$defs/Json'}, 'type': 'array'},
                {'type': 'string'},
                {'type': 'integer'},
                {'type': 'number'},
                {'type': 'boolean'},
                {'type': 'null'},
            ]
        }
    },
    '$ref': '#/$defs/Json',
}
"""
```

```python
from pydantic import TypeAdapter

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None  

ta = TypeAdapter(Json)
print(ta.json_schema())
"""
{
    '$defs': {
        'Json': {
            'anyOf': [
                {
                    'additionalProperties': {'$ref': '#/$defs/Json'},
                    'type': 'object',
                },
                {'items': {'$ref': '#/$defs/Json'}, 'type': 'array'},
                {'type': 'string'},
                {'type': 'integer'},
                {'type': 'number'},
                {'type': 'boolean'},
                {'type': 'null'},
            ]
        }
    },
    '$ref': '#/$defs/Json',
}
"""
```

1. The value of a named type alias is lazily evaluated, so there's no need to use forward annotations.

Tip

Pydantic defines a [`JsonValue`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.JsonValue) type as a convenience.

### Customizing validation with `__get_pydantic_core_schema__` [¶](https://docs.pydantic.dev/latest/concepts/types/#customizing-validation-with-__get_pydantic_core_schema__ "Permanent link")

To do more extensive customization of how Pydantic handles custom classes, and in particular when you have access to the class or can subclass it, you can implement a special `__get_pydantic_core_schema__` to tell Pydantic how to generate the `pydantic-core` schema.

While `pydantic` uses `pydantic-core` internally to handle validation and serialization, it is a new API for Pydantic V2, thus it is one of the areas most likely to be tweaked in the future and you should try to stick to the built-in constructs like those provided by `annotated-types`, `pydantic.Field`, or `BeforeValidator` and so on.

You can implement `__get_pydantic_core_schema__` both on a custom type and on metadata intended to be put in `Annotated`. In both cases the API is middleware-like and similar to that of "wrap" validators: you get a `source_type` (which isn't necessarily the same as the class, in particular for generics) and a `handler` that you can call with a type to either call the next metadata in `Annotated` or call into Pydantic's internal schema generation.

The simplest no-op implementation calls the handler with the type you are given, then returns that as the result. You can also choose to modify the type before calling the handler, modify the core schema returned by the handler, or not call the handler at all.

#### As a method on a custom type¶

The following is an example of a type that uses `__get_pydantic_core_schema__` to customize how it gets validated. This is equivalent to implementing `__get_validators__` in Pydantic V1.

```python
from typing import Any

from pydantic_core import CoreSchema, core_schema

from pydantic import GetCoreSchemaHandler, TypeAdapter

class Username(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))

ta = TypeAdapter(Username)
res = ta.validate_python('abc')
assert isinstance(res, Username)
assert res == 'abc'
```

See [JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/) for more details on how to customize JSON schemas for custom types.

#### As an annotation¶

Often you'll want to parametrize your custom type by more than just generic type parameters (which you can do via the type system and will be discussed later). Or you may not actually care (or want to) make an instance of your subclass; you actually want the original type, just with some extra validation done.

For example, if you were to implement `pydantic.AfterValidator` (see [Adding validation and serialization](https://docs.pydantic.dev/latest/concepts/types/#adding-validation-and-serialization)) yourself, you'd do something similar to the following:

```
from dataclasses import dataclass
from typing import Annotated, Any, Callable

from pydantic_core import CoreSchema, core_schema

from pydantic import BaseModel, GetCoreSchemaHandler

@dataclass(frozen=True)  
class MyAfterValidator:
    func: Callable[[Any], Any]

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            self.func, handler(source_type)
        )

Username = Annotated[str, MyAfterValidator(str.lower)]

class Model(BaseModel):
    name: Username

assert Model(name='ABC').name == 'abc'  
```

```python
from dataclasses import dataclass
from typing import Annotated, Any
from collections.abc import Callable

from pydantic_core import CoreSchema, core_schema

from pydantic import BaseModel, GetCoreSchemaHandler

@dataclass(frozen=True)  
class MyAfterValidator:
    func: Callable[[Any], Any]

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            self.func, handler(source_type)
        )

Username = Annotated[str, MyAfterValidator(str.lower)]

class Model(BaseModel):
    name: Username

assert Model(name='ABC').name == 'abc'  
```

1. The `frozen=True` specification makes `MyAfterValidator` hashable. Without this, a union such as `Username | None` will raise an error.
2. Notice that type checkers will not complain about assigning `'ABC'` to `Username` like they did in the previous example because they do not consider `Username` to be a distinct type from `str`.

#### Handling third-party types¶

Another use case for the pattern in the previous section is to handle third party types.

```python
from typing import Annotated, Any

from pydantic_core import core_schema

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)
from pydantic.json_schema import JsonSchemaValue

class ThirdPartyType:
    """
    This is meant to represent a type from a third-party library that wasn't designed with Pydantic
    integration in mind, and so doesn't have a \`pydantic_core.CoreSchema\` or anything.
    """

    x: int

    def __init__(self):
        self.x = 0

class _ThirdPartyTypePydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        We return a pydantic_core.CoreSchema that behaves in the following ways:

        * ints will be parsed as \`ThirdPartyType\` instances with the int as the x attribute
        * \`ThirdPartyType\` instances will be parsed as \`ThirdPartyType\` instances without any changes
        * Nothing else will pass validation
        * Serialization will always return just an int
        """

        def validate_from_int(value: int) -> ThirdPartyType:
            result = ThirdPartyType()
            result.x = value
            return result

        from_int_schema = core_schema.chain_schema(
            [
                core_schema.int_schema(),
                core_schema.no_info_plain_validator_function(validate_from_int),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_int_schema,
            python_schema=core_schema.union_schema(
                [
                    # check if it's an instance first before doing any further work
                    core_schema.is_instance_schema(ThirdPartyType),
                    from_int_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.x
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for \`int\`
        return handler(core_schema.int_schema())

# We now create an \`Annotated\` wrapper that we'll use as the annotation for fields on \`BaseModel\`s, etc.
PydanticThirdPartyType = Annotated[
    ThirdPartyType, _ThirdPartyTypePydanticAnnotation
]

# Create a model class that uses this annotation as a field
class Model(BaseModel):
    third_party_type: PydanticThirdPartyType

# Demonstrate that this field is handled correctly, that ints are parsed into \`ThirdPartyType\`, and that
# these instances are also "dumped" directly into ints as expected.
m_int = Model(third_party_type=1)
assert isinstance(m_int.third_party_type, ThirdPartyType)
assert m_int.third_party_type.x == 1
assert m_int.model_dump() == {'third_party_type': 1}

# Do the same thing where an instance of ThirdPartyType is passed in
instance = ThirdPartyType()
assert instance.x == 0
instance.x = 10

m_instance = Model(third_party_type=instance)
assert isinstance(m_instance.third_party_type, ThirdPartyType)
assert m_instance.third_party_type.x == 10
assert m_instance.model_dump() == {'third_party_type': 10}

# Demonstrate that validation errors are raised as expected for invalid inputs
try:
    Model(third_party_type='a')
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    third_party_type.is-instance[ThirdPartyType]
      Input should be an instance of ThirdPartyType [type=is_instance_of, input_value='a', input_type=str]
    third_party_type.chain[int,function-plain[validate_from_int()]]
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """

assert Model.model_json_schema() == {
    'properties': {
        'third_party_type': {'title': 'Third Party Type', 'type': 'integer'}
    },
    'required': ['third_party_type'],
    'title': 'Model',
    'type': 'object',
}
```

You can use this approach to e.g. define behavior for Pandas or Numpy types.

#### Using `GetPydanticSchema` to reduce boilerplate[¶](https://docs.pydantic.dev/latest/concepts/types/#using-getpydanticschema-to-reduce-boilerplate "Permanent link")

API Documentation

[`pydantic.types.GetPydanticSchema`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.GetPydanticSchema)  

You may notice that the above examples where we create a marker class require a good amount of boilerplate. For many simple cases you can greatly minimize this by using `pydantic.GetPydanticSchema`:

```python
from typing import Annotated

from pydantic_core import core_schema

from pydantic import BaseModel, GetPydanticSchema

class Model(BaseModel):
    y: Annotated[
        str,
        GetPydanticSchema(
            lambda tp, handler: core_schema.no_info_after_validator_function(
                lambda x: x * 2, handler(tp)
            )
        ),
    ]

assert Model(y='ab').y == 'abab'
```

#### Summary¶

Let's recap:

1. Pydantic provides high level hooks to customize types via `Annotated` like `AfterValidator` and `Field`. Use these when possible.
2. Under the hood these use `pydantic-core` to customize validation, and you can hook into that directly using `GetPydanticSchema` or a marker class with `__get_pydantic_core_schema__`.
3. If you really want a custom type you can implement `__get_pydantic_core_schema__` on the type itself.

### Handling custom generic classes¶

Warning

This is an advanced technique that you might not need in the beginning. In most of the cases you will probably be fine with standard Pydantic models.

You can use [Generic Classes](https://docs.python.org/3/library/typing.html#typing.Generic) as field types and perform custom validation based on the "type parameters" (or sub-types) with `__get_pydantic_core_schema__`.

If the Generic class that you are using as a sub-type has a classmethod `__get_pydantic_core_schema__`, you don't need to use [`arbitrary_types_allowed`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.arbitrary_types_allowed) for it to work.

Because the `source_type` parameter is not the same as the `cls` parameter, you can use `typing.get_args` (or `typing_extensions.get_args`) to extract the generic parameters. Then you can use the `handler` to generate a schema for them by calling `handler.generate_schema`. Note that we do not do something like `handler(get_args(source_type)[0])` because we want to generate an unrelated schema for that generic parameter, not one that is influenced by the current context of `Annotated` metadata and such. This is less important for custom types, but crucial for annotated metadata that modifies schema building.

```
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic_core import CoreSchema, core_schema
from typing_extensions import get_args, get_origin

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    ValidationError,
    ValidatorFunctionWrapHandler,
)

ItemType = TypeVar('ItemType')

# This is not a pydantic model, it's an arbitrary generic class
@dataclass
class Owner(Generic[ItemType]):
    name: str
    item: ItemType

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        origin = get_origin(source_type)
        if origin is None:  # used as \`x: Owner\` without params
            origin = source_type
            item_tp = Any
        else:
            item_tp = get_args(source_type)[0]
        # both calling handler(...) and handler.generate_schema(...)
        # would work, but prefer the latter for conceptual and consistency reasons
        item_schema = handler.generate_schema(item_tp)

        def val_item(
            v: Owner[Any], handler: ValidatorFunctionWrapHandler
        ) -> Owner[Any]:
            v.item = handler(v.item)
            return v

        python_schema = core_schema.chain_schema(
            # \`chain_schema\` means do the following steps in order:
            [
                # Ensure the value is an instance of Owner
                core_schema.is_instance_schema(cls),
                # Use the item_schema to validate \`items\`
                core_schema.no_info_wrap_validator_function(
                    val_item, item_schema
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            # for JSON accept an object with name and item keys
            json_schema=core_schema.chain_schema(
                [
                    core_schema.typed_dict_schema(
                        {
                            'name': core_schema.typed_dict_field(
                                core_schema.str_schema()
                            ),
                            'item': core_schema.typed_dict_field(item_schema),
                        }
                    ),
                    # after validating the json data convert it to python
                    core_schema.no_info_before_validator_function(
                        lambda data: Owner(
                            name=data['name'], item=data['item']
                        ),
                        # note that we reuse the same schema here as below
                        python_schema,
                    ),
                ]
            ),
            python_schema=python_schema,
        )

class Car(BaseModel):
    color: str

class House(BaseModel):
    rooms: int

class Model(BaseModel):
    car_owner: Owner[Car]
    home_owner: Owner[House]

model = Model(
    car_owner=Owner(name='John', item=Car(color='black')),
    home_owner=Owner(name='James', item=House(rooms=3)),
)
print(model)
"""
car_owner=Owner(name='John', item=Car(color='black')) home_owner=Owner(name='James', item=House(rooms=3))
"""

try:
    # If the values of the sub-types are invalid, we get an error
    Model(
        car_owner=Owner(name='John', item=House(rooms=3)),
        home_owner=Owner(name='James', item=Car(color='black')),
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    wine
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='Kinda good', input_type=str]
    cheese
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='yeah', input_type=str]
    """

# Similarly with JSON
model = Model.model_validate_json(
    '{"car_owner":{"name":"John","item":{"color":"black"}},"home_owner":{"name":"James","item":{"rooms":3}}}'
)
print(model)
"""
car_owner=Owner(name='John', item=Car(color='black')) home_owner=Owner(name='James', item=House(rooms=3))
"""

try:
    Model.model_validate_json(
        '{"car_owner":{"name":"John","item":{"rooms":3}},"home_owner":{"name":"James","item":{"color":"black"}}}'
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    car_owner.item.color
      Field required [type=missing, input_value={'rooms': 3}, input_type=dict]
    home_owner.item.rooms
      Field required [type=missing, input_value={'color': 'black'}, input_type=dict]
    """
```

```
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic_core import CoreSchema, core_schema
from typing import get_args, get_origin

from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    ValidationError,
    ValidatorFunctionWrapHandler,
)

ItemType = TypeVar('ItemType')

# This is not a pydantic model, it's an arbitrary generic class
@dataclass
class Owner(Generic[ItemType]):
    name: str
    item: ItemType

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        origin = get_origin(source_type)
        if origin is None:  # used as \`x: Owner\` without params
            origin = source_type
            item_tp = Any
        else:
            item_tp = get_args(source_type)[0]
        # both calling handler(...) and handler.generate_schema(...)
        # would work, but prefer the latter for conceptual and consistency reasons
        item_schema = handler.generate_schema(item_tp)

        def val_item(
            v: Owner[Any], handler: ValidatorFunctionWrapHandler
        ) -> Owner[Any]:
            v.item = handler(v.item)
            return v

        python_schema = core_schema.chain_schema(
            # \`chain_schema\` means do the following steps in order:
            [
                # Ensure the value is an instance of Owner
                core_schema.is_instance_schema(cls),
                # Use the item_schema to validate \`items\`
                core_schema.no_info_wrap_validator_function(
                    val_item, item_schema
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            # for JSON accept an object with name and item keys
            json_schema=core_schema.chain_schema(
                [
                    core_schema.typed_dict_schema(
                        {
                            'name': core_schema.typed_dict_field(
                                core_schema.str_schema()
                            ),
                            'item': core_schema.typed_dict_field(item_schema),
                        }
                    ),
                    # after validating the json data convert it to python
                    core_schema.no_info_before_validator_function(
                        lambda data: Owner(
                            name=data['name'], item=data['item']
                        ),
                        # note that we reuse the same schema here as below
                        python_schema,
                    ),
                ]
            ),
            python_schema=python_schema,
        )

class Car(BaseModel):
    color: str

class House(BaseModel):
    rooms: int

class Model(BaseModel):
    car_owner: Owner[Car]
    home_owner: Owner[House]

model = Model(
    car_owner=Owner(name='John', item=Car(color='black')),
    home_owner=Owner(name='James', item=House(rooms=3)),
)
print(model)
"""
car_owner=Owner(name='John', item=Car(color='black')) home_owner=Owner(name='James', item=House(rooms=3))
"""

try:
    # If the values of the sub-types are invalid, we get an error
    Model(
        car_owner=Owner(name='John', item=House(rooms=3)),
        home_owner=Owner(name='James', item=Car(color='black')),
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    wine
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='Kinda good', input_type=str]
    cheese
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='yeah', input_type=str]
    """

# Similarly with JSON
model = Model.model_validate_json(
    '{"car_owner":{"name":"John","item":{"color":"black"}},"home_owner":{"name":"James","item":{"rooms":3}}}'
)
print(model)
"""
car_owner=Owner(name='John', item=Car(color='black')) home_owner=Owner(name='James', item=House(rooms=3))
"""

try:
    Model.model_validate_json(
        '{"car_owner":{"name":"John","item":{"rooms":3}},"home_owner":{"name":"James","item":{"color":"black"}}}'
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Model
    car_owner.item.color
      Field required [type=missing, input_value={'rooms': 3}, input_type=dict]
    home_owner.item.rooms
      Field required [type=missing, input_value={'color': 'black'}, input_type=dict]
    """
```

#### Generic containers¶

The same idea can be applied to create generic container types, like a custom `Sequence` type:

```
from typing import Any, Sequence, TypeVar

from pydantic_core import ValidationError, core_schema
from typing_extensions import get_args

from pydantic import BaseModel, GetCoreSchemaHandler

T = TypeVar('T')

class MySequence(Sequence[T]):
    def __init__(self, v: Sequence[T]):
        self.v = v

    def __getitem__(self, i):
        return self.v[i]

    def __len__(self):
        return len(self.v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        instance_schema = core_schema.is_instance_schema(cls)

        args = get_args(source)
        if args:
            # replace the type and rely on Pydantic to generate the right schema
            # for \`Sequence\`
            sequence_t_schema = handler.generate_schema(Sequence[args[0]])
        else:
            sequence_t_schema = handler.generate_schema(Sequence)

        non_instance_schema = core_schema.no_info_after_validator_function(
            MySequence, sequence_t_schema
        )
        return core_schema.union_schema([instance_schema, non_instance_schema])

class M(BaseModel):
    model_config = dict(validate_default=True)

    s1: MySequence = [3]

m = M()
print(m)
#> s1=<__main__.MySequence object at 0x0123456789ab>
print(m.s1.v)
#> [3]

class M(BaseModel):
    s1: MySequence[int]

M(s1=[1])
try:
    M(s1=['a'])
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for M
    s1.is-instance[MySequence]
      Input should be an instance of MySequence [type=is_instance_of, input_value=['a'], input_type=list]
    s1.function-after[MySequence(), json-or-python[json=list[int],python=chain[is-instance[Sequence],function-wrap[sequence_validator()]]]].0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

```
from typing import Any, TypeVar
from collections.abc import Sequence

from pydantic_core import ValidationError, core_schema
from typing import get_args

from pydantic import BaseModel, GetCoreSchemaHandler

T = TypeVar('T')

class MySequence(Sequence[T]):
    def __init__(self, v: Sequence[T]):
        self.v = v

    def __getitem__(self, i):
        return self.v[i]

    def __len__(self):
        return len(self.v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        instance_schema = core_schema.is_instance_schema(cls)

        args = get_args(source)
        if args:
            # replace the type and rely on Pydantic to generate the right schema
            # for \`Sequence\`
            sequence_t_schema = handler.generate_schema(Sequence[args[0]])
        else:
            sequence_t_schema = handler.generate_schema(Sequence)

        non_instance_schema = core_schema.no_info_after_validator_function(
            MySequence, sequence_t_schema
        )
        return core_schema.union_schema([instance_schema, non_instance_schema])

class M(BaseModel):
    model_config = dict(validate_default=True)

    s1: MySequence = [3]

m = M()
print(m)
#> s1=<__main__.MySequence object at 0x0123456789ab>
print(m.s1.v)
#> [3]

class M(BaseModel):
    s1: MySequence[int]

M(s1=[1])
try:
    M(s1=['a'])
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for M
    s1.is-instance[MySequence]
      Input should be an instance of MySequence [type=is_instance_of, input_value=['a'], input_type=list]
    s1.function-after[MySequence(), json-or-python[json=list[int],python=chain[is-instance[Sequence],function-wrap[sequence_validator()]]]].0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

### Access to field name¶

Note

This was not possible with Pydantic V2 to V2.3, it was [re-added](https://github.com/pydantic/pydantic/pull/7542) in Pydantic V2.4.

As of Pydantic V2.4, you can access the field name via the `handler.field_name` within `__get_pydantic_core_schema__` and thereby set the field name which will be available from `info.field_name`.

```python
from typing import Any

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler, ValidationInfo

class CustomType:
    """Custom type that stores the field it was used in."""

    def __init__(self, value: int, field_name: str):
        self.value = value
        self.field_name = field_name

    def __repr__(self):
        return f'CustomType<{self.value} {self.field_name!r}>'

    @classmethod
    def validate(cls, value: int, info: ValidationInfo):
        return cls(value, info.field_name)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate, handler(int), field_name=handler.field_name
        )

class MyModel(BaseModel):
    my_field: CustomType

m = MyModel(my_field=1)
print(m.my_field)
#> CustomType<1 'my_field'>
```

You can also access `field_name` from the markers used with `Annotated`, like [`AfterValidator`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.AfterValidator).

```python
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ValidationInfo

def my_validators(value: int, info: ValidationInfo):
    return f'<{value} {info.field_name!r}>'

class MyModel(BaseModel):
    my_field: Annotated[int, AfterValidator(my_validators)]

m = MyModel(my_field=1)
print(m.my_field)
#> <1 'my_field'>
```

---
title: "Unions - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/unions/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
Unions are fundamentally different to all other types Pydantic validates - instead of requiring all fields/items/values to be valid, unions require only one member to be valid.

This leads to some nuance around how to validate unions:

- which member(s) of the union should you validate data against, and in which order?
- which errors to raise when validation fails?

Validating unions feels like adding another orthogonal dimension to the validation process.

To solve these problems, Pydantic supports three fundamental approaches to validating unions:

1. [left to right mode](https://docs.pydantic.dev/latest/concepts/unions/#left-to-right-mode) - the simplest approach, each member of the union is tried in order and the first match is returned
2. [smart mode](https://docs.pydantic.dev/latest/concepts/unions/#smart-mode) - similar to "left to right mode" members are tried in order; however, validation will proceed past the first match to attempt to find a better match, this is the default mode for most union validation
3. [discriminated unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions) - only one member of the union is tried, based on a discriminator

Tip

In general, we recommend using [discriminated unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions). They are both more performant and more predictable than untagged unions, as they allow you to control which member of the union to validate against.

For complex cases, if you're using untagged unions, it's recommended to use `union_mode='left_to_right'` if you need guarantees about the order of validation attempts against the union members.

If you're looking for incredibly specialized behavior, you can use a [custom validator](https://docs.pydantic.dev/latest/concepts/validators/#field-validators).

## Union Modes¶
### Left to Right Mode¶

Note

Because this mode often leads to unexpected validation results, it is not the default in Pydantic >=2, instead `union_mode='smart'` is the default.

With this approach, validation is attempted against each member of the union in their order they're defined, and the first successful validation is accepted as input.

If validation fails on all members, the validation error includes the errors from all members of the union.

`union_mode='left_to_right'` must be set as a [`Field`](https://docs.pydantic.dev/latest/concepts/fields/) parameter on union fields where you want to use it.

Union with left to right mode

```
from typing import Union

from pydantic import BaseModel, Field, ValidationError

class User(BaseModel):
    id: Union[str, int] = Field(union_mode='left_to_right')

print(User(id=123))
#> id=123
print(User(id='hello'))
#> id='hello'

try:
    User(id=[])
except ValidationError as e:
    print(e)
    """
    2 validation errors for User
    id.str
      Input should be a valid string [type=string_type, input_value=[], input_type=list]
    id.int
      Input should be a valid integer [type=int_type, input_value=[], input_type=list]
    """
```

Union with left to right mode

```
from pydantic import BaseModel, Field, ValidationError

class User(BaseModel):
    id: str | int = Field(union_mode='left_to_right')

print(User(id=123))
#> id=123
print(User(id='hello'))
#> id='hello'

try:
    User(id=[])
except ValidationError as e:
    print(e)
    """
    2 validation errors for User
    id.str
      Input should be a valid string [type=string_type, input_value=[], input_type=list]
    id.int
      Input should be a valid integer [type=int_type, input_value=[], input_type=list]
    """
```

The order of members is very important in this case, as demonstrated by tweak the above example:

Union with left to right - unexpected results

```
from typing import Union

from pydantic import BaseModel, Field

class User(BaseModel):
    id: Union[int, str] = Field(union_mode='left_to_right')

print(User(id=123))  # 
#> id=123
print(User(id='456'))  # 
#> id=456
```

Union with left to right - unexpected results

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int | str = Field(union_mode='left_to_right')

print(User(id=123))  # 
#> id=123
print(User(id='456'))  # 
#> id=456
```

1. As expected the input is validated against the `int` member and the result is as expected.
2. We're in lax mode and the numeric string `'123'` is valid as input to the first member of the union, `int`. Since that is tried first, we get the surprising result of `id` being an `int` instead of a `str`.

### Smart Mode¶

Because of the potentially surprising results of `union_mode='left_to_right'`, in Pydantic >=2 the default mode for `Union` validation is `union_mode='smart'`.

In this mode, pydantic attempts to select the best match for the input from the union members. The exact algorithm may change between Pydantic minor releases to allow for improvements in both performance and accuracy.

Note

We reserve the right to tweak the internal `smart` matching algorithm in future versions of Pydantic. If you rely on very specific matching behavior, it's recommended to use `union_mode='left_to_right'` or [discriminated unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions).

Smart Mode Algorithm

The smart mode algorithm uses two metrics to determine the best match for the input:

1. The number of valid fields set (relevant for models, dataclasses, and typed dicts)
2. The exactness of the match (relevant for all types)

#### Number of valid fields set¶

Note

This metric was introduced in Pydantic v2.8.0. Prior to this version, only exactness was used to determine the best match.

This metric is currently only relevant for models, dataclasses, and typed dicts.

The greater the number of valid fields set, the better the match. The number of fields set on nested models is also taken into account. These counts bubble up to the top-level union, where the union member with the highest count is considered the best match.

For data types where this metric is relevant, we prioritize this count over exactness. For all other types, we use solely exactness.

#### Exactness¶

For `exactness`, Pydantic scores a match of a union member into one of the following three groups (from highest score to lowest score):

- An exact type match, for example an `int` input to a `float | int` union validation is an exact type match for the `int` member
- Validation would have succeeded in [`strict` mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- Validation would have succeeded in lax mode

The union match which produced the highest exactness score will be considered the best match.

In smart mode, the following steps are taken to try to select the best match for the input:

1. Union members are attempted left to right, with any successful matches scored into one of the three exactness categories described above, with the valid fields set count also tallied.
2. After all members have been evaluated, the member with the highest "valid fields set" count is returned.
3. If there's a tie for the highest "valid fields set" count, the exactness score is used as a tiebreaker, and the member with the highest exactness score is returned.
4. If validation failed on all the members, return all the errors.

5. Union members are attempted left to right, with any successful matches scored into one of the three exactness categories described above.
- If validation succeeds with an exact type match, that member is returned immediately and following members will not be attempted.
2. If validation succeeded on at least one member as a "strict" match, the leftmost of those "strict" matches is returned.
3. If validation succeeded on at least one member in "lax" mode, the leftmost match is returned.
4. Validation failed on all the members, return all the errors.

```
from typing import Union
from uuid import UUID

from pydantic import BaseModel

class User(BaseModel):
    id: Union[int, str, UUID]
    name: str

user_01 = User(id=123, name='John Doe')
print(user_01)
#> id=123 name='John Doe'
print(user_01.id)
#> 123
user_02 = User(id='1234', name='John Doe')
print(user_02)
#> id='1234' name='John Doe'
print(user_02.id)
#> 1234
user_03_uuid = UUID('cf57432e-809e-4353-adbd-9d5c0d733868')
user_03 = User(id=user_03_uuid, name='John Doe')
print(user_03)
#> id=UUID('cf57432e-809e-4353-adbd-9d5c0d733868') name='John Doe'
print(user_03.id)
#> cf57432e-809e-4353-adbd-9d5c0d733868
print(user_03_uuid.int)
#> 275603287559914445491632874575877060712
```

```
from uuid import UUID

from pydantic import BaseModel

class User(BaseModel):
    id: int | str | UUID
    name: str

user_01 = User(id=123, name='John Doe')
print(user_01)
#> id=123 name='John Doe'
print(user_01.id)
#> 123
user_02 = User(id='1234', name='John Doe')
print(user_02)
#> id='1234' name='John Doe'
print(user_02.id)
#> 1234
user_03_uuid = UUID('cf57432e-809e-4353-adbd-9d5c0d733868')
user_03 = User(id=user_03_uuid, name='John Doe')
print(user_03)
#> id=UUID('cf57432e-809e-4353-adbd-9d5c0d733868') name='John Doe'
print(user_03.id)
#> cf57432e-809e-4353-adbd-9d5c0d733868
print(user_03_uuid.int)
#> 275603287559914445491632874575877060712
```

## Discriminated Unions¶

**Discriminated unions are sometimes referred to as "Tagged Unions".**

We can use discriminated unions to more efficiently validate `Union` types, by choosing which member of the union to validate against.

This makes validation more efficient and also avoids a proliferation of errors when validation fails.

Adding discriminator to unions also means the generated JSON schema implements the [associated OpenAPI specification](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#discriminator-object).

### Discriminated Unions with `str` discriminators[¶](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-str-discriminators "Permanent link")

Frequently, in the case of a `Union` with multiple models, there is a common field to all members of the union that can be used to distinguish which union case the data should be validated against; this is referred to as the "discriminator" in [OpenAPI](https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/).

To validate models based on that information you can set the same field - let's call it `my_discriminator` - in each of the models with a discriminated value, which is one (or many) `Literal` value(s). For your `Union`, you can set the discriminator in its value: `Field(discriminator='my_discriminator')`.

```
from typing import Literal, Union

from pydantic import BaseModel, Field, ValidationError

class Cat(BaseModel):
    pet_type: Literal['cat']
    meows: int

class Dog(BaseModel):
    pet_type: Literal['dog']
    barks: float

class Lizard(BaseModel):
    pet_type: Literal['reptile', 'lizard']
    scales: bool

class Model(BaseModel):
    pet: Union[Cat, Dog, Lizard] = Field(discriminator='pet_type')
    n: int

print(Model(pet={'pet_type': 'dog', 'barks': 3.14}, n=1))
#> pet=Dog(pet_type='dog', barks=3.14) n=1
try:
    Model(pet={'pet_type': 'dog'}, n=1)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.dog.barks
      Field required [type=missing, input_value={'pet_type': 'dog'}, input_type=dict]
    """
```

```
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

class Cat(BaseModel):
    pet_type: Literal['cat']
    meows: int

class Dog(BaseModel):
    pet_type: Literal['dog']
    barks: float

class Lizard(BaseModel):
    pet_type: Literal['reptile', 'lizard']
    scales: bool

class Model(BaseModel):
    pet: Cat | Dog | Lizard = Field(discriminator='pet_type')
    n: int

print(Model(pet={'pet_type': 'dog', 'barks': 3.14}, n=1))
#> pet=Dog(pet_type='dog', barks=3.14) n=1
try:
    Model(pet={'pet_type': 'dog'}, n=1)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.dog.barks
      Field required [type=missing, input_value={'pet_type': 'dog'}, input_type=dict]
    """
```

### Discriminated Unions with callable `Discriminator`[¶](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-callable-discriminator "Permanent link")

API Documentation

[`pydantic.types.Discriminator`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.Discriminator)  

In the case of a `Union` with multiple models, sometimes there isn't a single uniform field across all models that you can use as a discriminator. This is the perfect use case for a callable `Discriminator`.

Tip

When you're designing callable discriminators, remember that you might have to account for both `dict` and model type inputs. This pattern is similar to that of `mode='before'` validators, where you have to anticipate various forms of input.

But wait! You ask, I only anticipate passing in `dict` types, why do I need to account for models? Pydantic uses callable discriminators for serialization as well, at which point the input to your callable is very likely to be a model instance.

In the following examples, you'll see that the callable discriminators are designed to handle both `dict` and model inputs. If you don't follow this practice, it's likely that you'll, in the best case, get warnings during serialization, and in the worst case, get runtime errors during validation.

```
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Discriminator, Tag

class Pie(BaseModel):
    time_to_cook: int
    num_ingredients: int

class ApplePie(Pie):
    fruit: Literal['apple'] = 'apple'

class PumpkinPie(Pie):
    filling: Literal['pumpkin'] = 'pumpkin'

def get_discriminator_value(v: Any) -> str:
    if isinstance(v, dict):
        return v.get('fruit', v.get('filling'))
    return getattr(v, 'fruit', getattr(v, 'filling', None))

class ThanksgivingDinner(BaseModel):
    dessert: Annotated[
        Union[
            Annotated[ApplePie, Tag('apple')],
            Annotated[PumpkinPie, Tag('pumpkin')],
        ],
        Discriminator(get_discriminator_value),
    ]

apple_variation = ThanksgivingDinner.model_validate(
    {'dessert': {'fruit': 'apple', 'time_to_cook': 60, 'num_ingredients': 8}}
)
print(repr(apple_variation))
"""
ThanksgivingDinner(dessert=ApplePie(time_to_cook=60, num_ingredients=8, fruit='apple'))
"""

pumpkin_variation = ThanksgivingDinner.model_validate(
    {
        'dessert': {
            'filling': 'pumpkin',
            'time_to_cook': 40,
            'num_ingredients': 6,
        }
    }
)
print(repr(pumpkin_variation))
"""
ThanksgivingDinner(dessert=PumpkinPie(time_to_cook=40, num_ingredients=6, filling='pumpkin'))
"""
```

```
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Discriminator, Tag

class Pie(BaseModel):
    time_to_cook: int
    num_ingredients: int

class ApplePie(Pie):
    fruit: Literal['apple'] = 'apple'

class PumpkinPie(Pie):
    filling: Literal['pumpkin'] = 'pumpkin'

def get_discriminator_value(v: Any) -> str:
    if isinstance(v, dict):
        return v.get('fruit', v.get('filling'))
    return getattr(v, 'fruit', getattr(v, 'filling', None))

class ThanksgivingDinner(BaseModel):
    dessert: Annotated[
        (
            Annotated[ApplePie, Tag('apple')] |
            Annotated[PumpkinPie, Tag('pumpkin')]
        ),
        Discriminator(get_discriminator_value),
    ]

apple_variation = ThanksgivingDinner.model_validate(
    {'dessert': {'fruit': 'apple', 'time_to_cook': 60, 'num_ingredients': 8}}
)
print(repr(apple_variation))
"""
ThanksgivingDinner(dessert=ApplePie(time_to_cook=60, num_ingredients=8, fruit='apple'))
"""

pumpkin_variation = ThanksgivingDinner.model_validate(
    {
        'dessert': {
            'filling': 'pumpkin',
            'time_to_cook': 40,
            'num_ingredients': 6,
        }
    }
)
print(repr(pumpkin_variation))
"""
ThanksgivingDinner(dessert=PumpkinPie(time_to_cook=40, num_ingredients=6, filling='pumpkin'))
"""
```

`Discriminator`s can also be used to validate `Union` types with combinations of models and primitive types.

For example:

```
from typing import Annotated, Any, Union

from pydantic import BaseModel, Discriminator, Tag, ValidationError

def model_x_discriminator(v: Any) -> str:
    if isinstance(v, int):
        return 'int'
    if isinstance(v, (dict, BaseModel)):
        return 'model'
    else:
        # return None if the discriminator value isn't found
        return None

class SpecialValue(BaseModel):
    value: int

class DiscriminatedModel(BaseModel):
    value: Annotated[
        Union[
            Annotated[int, Tag('int')],
            Annotated['SpecialValue', Tag('model')],
        ],
        Discriminator(model_x_discriminator),
    ]

model_data = {'value': {'value': 1}}
m = DiscriminatedModel.model_validate(model_data)
print(m)
#> value=SpecialValue(value=1)

int_data = {'value': 123}
m = DiscriminatedModel.model_validate(int_data)
print(m)
#> value=123

try:
    DiscriminatedModel.model_validate({'value': 'not an int or a model'})
except ValidationError as e:
    print(e)  
    """
    1 validation error for DiscriminatedModel
    value
      Unable to extract tag using discriminator model_x_discriminator() [type=union_tag_not_found, input_value='not an int or a model', input_type=str]
    """
```

```python
from typing import Annotated, Any

from pydantic import BaseModel, Discriminator, Tag, ValidationError

def model_x_discriminator(v: Any) -> str:
    if isinstance(v, int):
        return 'int'
    if isinstance(v, (dict, BaseModel)):
        return 'model'
    else:
        # return None if the discriminator value isn't found
        return None

class SpecialValue(BaseModel):
    value: int

class DiscriminatedModel(BaseModel):
    value: Annotated[
        (
            Annotated[int, Tag('int')] |
            Annotated['SpecialValue', Tag('model')]
        ),
        Discriminator(model_x_discriminator),
    ]

model_data = {'value': {'value': 1}}
m = DiscriminatedModel.model_validate(model_data)
print(m)
#> value=SpecialValue(value=1)

int_data = {'value': 123}
m = DiscriminatedModel.model_validate(int_data)
print(m)
#> value=123

try:
    DiscriminatedModel.model_validate({'value': 'not an int or a model'})
except ValidationError as e:
    print(e)  
    """
    1 validation error for DiscriminatedModel
    value
      Unable to extract tag using discriminator model_x_discriminator() [type=union_tag_not_found, input_value='not an int or a model', input_type=str]
    """
```

1. Notice the callable discriminator function returns `None` if a discriminator value is not found. When `None` is returned, this `union_tag_not_found` error is raised.

Note

Using the [annotated pattern](https://docs.pydantic.dev/latest/concepts/fields/#the-annotated-pattern) can be handy to regroup the `Union` and `discriminator` information. See the next example for more details.

There are a few ways to set a discriminator for a field, all varying slightly in syntax.

For `str` discriminators:

```python
some_field: Union[...] = Field(discriminator='my_discriminator')
some_field: Annotated[Union[...], Field(discriminator='my_discriminator')]
```

For callable `Discriminator`s:

```python
some_field: Union[...] = Field(discriminator=Discriminator(...))
some_field: Annotated[Union[...], Discriminator(...)]
some_field: Annotated[Union[...], Field(discriminator=Discriminator(...))]
```

Warning

Discriminated unions cannot be used with only a single variant, such as `Union[Cat]`.

Python changes `Union[T]` into `T` at interpretation time, so it is not possible for `pydantic` to distinguish fields of `Union[T]` from `T`.

### Nested Discriminated Unions¶

Only one discriminator can be set for a field but sometimes you want to combine multiple discriminators. You can do it by creating nested `Annotated` types, e.g.:

```python
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, ValidationError

class BlackCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['black']
    black_name: str

class WhiteCat(BaseModel):
    pet_type: Literal['cat']
    color: Literal['white']
    white_name: str

Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

class Dog(BaseModel):
    pet_type: Literal['dog']
    name: str

Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]

class Model(BaseModel):
    pet: Pet
    n: int

m = Model(pet={'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}, n=1)
print(m)
#> pet=BlackCat(pet_type='cat', color='black', black_name='felix') n=1
try:
    Model(pet={'pet_type': 'cat', 'color': 'red'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat
      Input tag 'red' found using 'color' does not match any of the expected tags: 'black', 'white' [type=union_tag_invalid, input_value={'pet_type': 'cat', 'color': 'red'}, input_type=dict]
    """
try:
    Model(pet={'pet_type': 'cat', 'color': 'black'}, n='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet.cat.black.black_name
      Field required [type=missing, input_value={'pet_type': 'cat', 'color': 'black'}, input_type=dict]
    """
```

Tip

If you want to validate data against a union, and solely a union, you can use pydantic's [`TypeAdapter`](https://docs.pydantic.dev/latest/concepts/type_adapter/) construct instead of inheriting from the standard `BaseModel`.

In the context of the previous example, we have the following:

```python
type_adapter = TypeAdapter(Pet)

pet = type_adapter.validate_python(
    {'pet_type': 'cat', 'color': 'black', 'black_name': 'felix'}
)
print(repr(pet))
#> BlackCat(pet_type='cat', color='black', black_name='felix')
```

## Union Validation Errors¶

When `Union` validation fails, error messages can be quite verbose, as they will produce validation errors for each case in the union. This is especially noticeable when dealing with recursive models, where reasons may be generated at each level of recursion. Discriminated unions help to simplify error messages in this case, as validation errors are only produced for the case with a matching discriminator value.

You can also customize the error type, message, and context for a `Discriminator` by passing these specifications as parameters to the `Discriminator` constructor, as seen in the example below.

```python
from typing import Annotated, Union

from pydantic import BaseModel, Discriminator, Tag, ValidationError

# Errors are quite verbose with a normal Union:
class Model(BaseModel):
    x: Union[str, 'Model']

try:
    Model.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as e:
    print(e)
    """
    4 validation errors for Model
    x.str
      Input should be a valid string [type=string_type, input_value={'x': {'x': 1}}, input_type=dict]
    x.Model.x.str
      Input should be a valid string [type=string_type, input_value={'x': 1}, input_type=dict]
    x.Model.x.Model.x.str
      Input should be a valid string [type=string_type, input_value=1, input_type=int]
    x.Model.x.Model.x.Model
      Input should be a valid dictionary or instance of Model [type=model_type, input_value=1, input_type=int]
    """

try:
    Model.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as e:
    print(e)
    """
    4 validation errors for Model
    x.str
      Input should be a valid string [type=string_type, input_value={'x': {'x': {}}}, input_type=dict]
    x.Model.x.str
      Input should be a valid string [type=string_type, input_value={'x': {}}, input_type=dict]
    x.Model.x.Model.x.str
      Input should be a valid string [type=string_type, input_value={}, input_type=dict]
    x.Model.x.Model.x.Model.x
      Field required [type=missing, input_value={}, input_type=dict]
    """

# Errors are much simpler with a discriminated union:
def model_x_discriminator(v):
    if isinstance(v, str):
        return 'str'
    if isinstance(v, (dict, BaseModel)):
        return 'model'

class DiscriminatedModel(BaseModel):
    x: Annotated[
        Union[
            Annotated[str, Tag('str')],
            Annotated['DiscriminatedModel', Tag('model')],
        ],
        Discriminator(
            model_x_discriminator,
            custom_error_type='invalid_union_member',  
            custom_error_message='Invalid union member',  
            custom_error_context={'discriminator': 'str_or_model'},  
        ),
    ]

try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': 1}}})
except ValidationError as e:
    print(e)
    """
    1 validation error for DiscriminatedModel
    x.model.x.model.x
      Invalid union member [type=invalid_union_member, input_value=1, input_type=int]
    """

try:
    DiscriminatedModel.model_validate({'x': {'x': {'x': {}}}})
except ValidationError as e:
    print(e)
    """
    1 validation error for DiscriminatedModel
    x.model.x.model.x.model.x
      Field required [type=missing, input_value={}, input_type=dict]
    """

# The data is still handled properly when valid:
data = {'x': {'x': {'x': 'a'}}}
m = DiscriminatedModel.model_validate(data)
print(m.model_dump())
#> {'x': {'x': {'x': 'a'}}}
```

You can also simplify error messages by labeling each case with a [`Tag`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.Tag). This is especially useful when you have complex types like those in this example:

```python
from typing import Annotated, Union

from pydantic import AfterValidator, Tag, TypeAdapter, ValidationError

DoubledList = Annotated[list[int], AfterValidator(lambda x: x * 2)]
StringsMap = dict[str, str]

# Not using any \`Tag\`s for each union case, the errors are not so nice to look at
adapter = TypeAdapter(Union[DoubledList, StringsMap])

try:
    adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[function-after[<lambda>(), list[int]],dict[str,str]]
    function-after[<lambda>(), list[int]].0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    dict[str,str]
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """

tag_adapter = TypeAdapter(
    Union[
        Annotated[DoubledList, Tag('DoubledList')],
        Annotated[StringsMap, Tag('StringsMap')],
    ]
)

try:
    tag_adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[DoubledList,StringsMap]
    DoubledList.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    StringsMap
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """
```
---
title: "Alias - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/alias/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
An alias is an alternative name for a field, used when serializing and deserializing data.

You can specify an alias in the following ways:

- `alias` on the [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field)
- must be a `str`
- `validation_alias` on the [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field)
- can be an instance of `str`, [`AliasPath`](https://docs.pydantic.dev/latest/api/aliases/#pydantic.aliases.AliasPath), or [`AliasChoices`](https://docs.pydantic.dev/latest/api/aliases/#pydantic.aliases.AliasChoices)
- `serialization_alias` on the [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field)
- must be a `str`
- `alias_generator` on the [`Config`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.alias_generator)
- can be a callable or an instance of [`AliasGenerator`](https://docs.pydantic.dev/latest/api/aliases/#pydantic.aliases.AliasGenerator)

For examples of how to use `alias`, `validation_alias`, and `serialization_alias`, see [Field aliases](https://docs.pydantic.dev/latest/concepts/fields/#field-aliases).

## `AliasPath` and `AliasChoices`[¶](https://docs.pydantic.dev/latest/concepts/alias/#aliaspath-and-aliaschoices "Permanent link")

API Documentation

[`pydantic.aliases.AliasPath`](https://docs.pydantic.dev/latest/api/aliases/#pydantic.aliases.AliasPath)  
[`pydantic.aliases.AliasChoices`](https://docs.pydantic.dev/latest/api/aliases/#pydantic.aliases.AliasChoices)  

Pydantic provides two special types for convenience when using `validation_alias`: `AliasPath` and `AliasChoices`.

The `AliasPath` is used to specify a path to a field using aliases. For example:

```python
from pydantic import BaseModel, Field, AliasPath

class User(BaseModel):
    first_name: str = Field(validation_alias=AliasPath('names', 0))
    last_name: str = Field(validation_alias=AliasPath('names', 1))

user = User.model_validate({'names': ['John', 'Doe']})  
print(user)
#> first_name='John' last_name='Doe'
```

In the `'first_name'` field, we are using the alias `'names'` and the index `0` to specify the path to the first name. In the `'last_name'` field, we are using the alias `'names'` and the index `1` to specify the path to the last name.

`AliasChoices` is used to specify a choice of aliases. For example:

```python
from pydantic import BaseModel, Field, AliasChoices

class User(BaseModel):
    first_name: str = Field(validation_alias=AliasChoices('first_name', 'fname'))
    last_name: str = Field(validation_alias=AliasChoices('last_name', 'lname'))

user = User.model_validate({'fname': 'John', 'lname': 'Doe'})  
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'first_name': 'John', 'lname': 'Doe'})  
print(user)
#> first_name='John' last_name='Doe'
```

You can also use `AliasChoices` with `AliasPath`:

```python
from pydantic import BaseModel, Field, AliasPath, AliasChoices

class User(BaseModel):
    first_name: str = Field(validation_alias=AliasChoices('first_name', AliasPath('names', 0)))
    last_name: str = Field(validation_alias=AliasChoices('last_name', AliasPath('names', 1)))

user = User.model_validate({'first_name': 'John', 'last_name': 'Doe'})
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'names': ['John', 'Doe']})
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'names': ['John'], 'last_name': 'Doe'})
print(user)
#> first_name='John' last_name='Doe'
```

## Using alias generators¶

You can use the `alias_generator` parameter of [`Config`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.alias_generator) to specify a callable (or group of callables, via `AliasGenerator`) that will generate aliases for all fields in a model. This is useful if you want to use a consistent naming convention for all fields in a model, but do not want to specify the alias for each field individually.

### Using a callable¶

Here's a basic example using a callable:

```python
from pydantic import BaseModel, ConfigDict

class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: field_name.upper()
    )

    age: int
    height: float
    kind: str

t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'}
```

### Using an `AliasGenerator`[¶](https://docs.pydantic.dev/latest/concepts/alias/#using-an-aliasgenerator "Permanent link")

API Documentation

[`pydantic.aliases.AliasGenerator`](https://docs.pydantic.dev/latest/api/aliases/#pydantic.aliases.AliasGenerator)  

`AliasGenerator` is a class that allows you to specify multiple alias generators for a model. You can use an `AliasGenerator` to specify different alias generators for validation and serialization.

This is particularly useful if you need to use different naming conventions for loading and saving data, but you don't want to specify the validation and serialization aliases for each field individually.

For example:

```python
from pydantic import AliasGenerator, BaseModel, ConfigDict

class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: field_name.upper(),
            serialization_alias=lambda field_name: field_name.title(),
        )
    )

    age: int
    height: float
    kind: str

t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'Age': 12, 'Height': 1.2, 'Kind': 'oak'}
```

## Alias Precedence¶

If you specify an `alias` on the [`Field`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field), it will take precedence over the generated alias by default:

```python
from pydantic import BaseModel, ConfigDict, Field

def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))

class Voice(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str
    language_code: str = Field(alias='lang')

voice = Voice(Name='Filiz', lang='tr-TR')
print(voice.language_code)
#> tr-TR
print(voice.model_dump(by_alias=True))
#> {'Name': 'Filiz', 'lang': 'tr-TR'}
```

### Alias Priority¶

You may set `alias_priority` on a field to change this behavior:

- `alias_priority=2` the alias will *not* be overridden by the alias generator.
- `alias_priority=1` the alias *will* be overridden by the alias generator.
- `alias_priority` not set:
- alias is set: the alias will *not* be overridden by the alias generator.
- alias is not set: the alias *will* be overridden by the alias generator.

The same precedence applies to `validation_alias` and `serialization_alias`. See more about the different field aliases under [field aliases](https://docs.pydantic.dev/latest/concepts/fields/#field-aliases).

## Alias Configuration¶

You can use [`ConfigDict`](https://docs.pydantic.dev/latest/concepts/config/) settings or runtime validation/serialization settings to control whether or not aliases are used.

### `ConfigDict` Settings[¶](https://docs.pydantic.dev/latest/concepts/alias/#configdict-settings "Permanent link")

You can use [configuration settings](https://docs.pydantic.dev/latest/concepts/config/) to control, at the model level, whether or not aliases are used for validation and serialization. If you would like to control this behavior for nested models/surpassing the config-model boundary, use [runtime settings](https://docs.pydantic.dev/latest/concepts/alias/#runtime-settings).

#### Validation¶

When validating data, you can enable population of attributes by attribute name, alias, or both. **By default**, Pydantic uses aliases for validation. Further configuration is available via:

- [`ConfigDict.validate_by_alias`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.validate_by_alias): `True` by default
- [`ConfigDict.validate_by_name`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.validate_by_name): `False` by default

```
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    my_field: str = Field(validation_alias='my_alias')

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=False)

print(repr(Model(my_alias='foo')))  
#> Model(my_field='foo')
```

```python
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    my_field: str = Field(validation_alias='my_alias')

    model_config = ConfigDict(validate_by_alias=False, validate_by_name=True)

print(repr(Model(my_field='foo')))  
#> Model(my_field='foo')
```

1. the attribute identifier `my_field` is used for validation.

```python
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    my_field: str = Field(validation_alias='my_alias')

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

print(repr(Model(my_alias='foo')))  
#> Model(my_field='foo')

print(repr(Model(my_field='foo')))  
#> Model(my_field='foo')
```

1. The alias `my_alias` is used for validation.
2. the attribute identifier `my_field` is used for validation.

Warning

You cannot set both `validate_by_alias` and `validate_by_name` to `False`. A [user error](https://docs.pydantic.dev/latest/errors/usage_errors/#validate-by-alias-and-name-false) is raised in this case.

#### Serialization¶

When serializing data, you can enable serialization by alias, which is disabled by default. See the [`ConfigDict.serialize_by_alias`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.serialize_by_alias) API documentation for more details.

```python
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    my_field: str = Field(serialization_alias='my_alias')

    model_config = ConfigDict(serialize_by_alias=True)

m = Model(my_field='foo')
print(m.model_dump())  
#> {'my_alias': 'foo'}
```

Note

The fact that serialization by alias is disabled by default is notably inconsistent with the default for validation (where aliases are used by default). We anticipate changing this default in V3.

### Runtime Settings¶

You can use runtime alias flags to control alias use for validation and serialization on a per-call basis. If you would like to control this behavior on a model level, use [`ConfigDict` settings](https://docs.pydantic.dev/latest/concepts/alias/#configdict-settings).

#### Validation¶

When validating data, you can enable population of attributes by attribute name, alias, or both.

The `by_alias` and `by_name` flags are available on the [`model_validate()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate), [`model_validate_json()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_json), and [`model_validate_strings()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate_strings) methods, as well as the [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) validation methods.

By default:

- `by_alias` is `True`
- `by_name` is `False`

```
from pydantic import BaseModel, Field

class Model(BaseModel):
    my_field: str = Field(validation_alias='my_alias')

m = Model.model_validate(
    {'my_alias': 'foo'},  
    by_alias=True,
    by_name=False,
)
print(repr(m))
#> Model(my_field='foo')
```

```python
from pydantic import BaseModel, Field

class Model(BaseModel):
    my_field: str = Field(validation_alias='my_alias')

m = Model.model_validate(
    {'my_field': 'foo'}, by_alias=False, by_name=True  
)
print(repr(m))
#> Model(my_field='foo')
```

1. The attribute name `my_field` is used for validation.

```python
from pydantic import BaseModel, Field

class Model(BaseModel):
    my_field: str = Field(validation_alias='my_alias')

m = Model.model_validate(
    {'my_alias': 'foo'}, by_alias=True, by_name=True  
)
print(repr(m))
#> Model(my_field='foo')

m = Model.model_validate(
    {'my_field': 'foo'}, by_alias=True, by_name=True  
)
print(repr(m))
#> Model(my_field='foo')
```

1. The alias `my_alias` is used for validation.
2. The attribute name `my_field` is used for validation.

Warning

You cannot set both `by_alias` and `by_name` to `False`. A [user error](https://docs.pydantic.dev/latest/errors/usage_errors/#validate-by-alias-and-name-false) is raised in this case.

#### Serialization¶

When serializing data, you can enable serialization by alias via the `by_alias` flag which is available on the [`model_dump()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump) and [`model_dump_json()`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json) methods, as well as the [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) ones.

By default, `by_alias` is `False`.

```py
from pydantic import BaseModel, Field

class Model(BaseModel):
    my_field: str = Field(serialization_alias='my_alias')

m = Model(my_field='foo')
print(m.model_dump(by_alias=True))  
#> {'my_alias': 'foo'}
```

Note

The fact that serialization by alias is disabled by default is notably inconsistent with the default for validation (where aliases are used by default). We anticipate changing this default in V3.

---
title: "Configuration - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/config/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
The behaviour of Pydantic can be controlled via a variety of configuration values, documented on the [`ConfigDict`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict) class. This page describes how configuration can be specified for Pydantic's supported types.

## Configuration on Pydantic models¶

On Pydantic models, configuration can be specified in two ways:

- Using the [`model_config`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_config) class attribute:

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class Model(BaseModel):
    model_config = ConfigDict(str_max_length=5)  

    v: str

try:
    m = Model(v='abcdef')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    v
      String should have at most 5 characters [type=string_too_long, input_value='abcdef', input_type=str]
    """
```

Note

In Pydantic V1, the `Config` class was used. This is still supported, but **deprecated**.
- Using class arguments:

```python
from pydantic import BaseModel

class Model(BaseModel, frozen=True):
    a: str  
```

## Configuration on Pydantic dataclasses¶

[Pydantic dataclasses](https://docs.pydantic.dev/latest/concepts/dataclasses/) also support configuration (read more in the [dedicated section](https://docs.pydantic.dev/latest/concepts/dataclasses/#dataclass-config)).

```python
from pydantic import ConfigDict, ValidationError
from pydantic.dataclasses import dataclass

@dataclass(config=ConfigDict(str_max_length=10, validate_assignment=True))
class User:
    name: str

user = User(name='John Doe')
try:
    user.name = 'x' * 20
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      String should have at most 10 characters [type=string_too_long, input_value='xxxxxxxxxxxxxxxxxxxx', input_type=str]
    """
```

## Configuration on `TypeAdapter`[¶](https://docs.pydantic.dev/latest/concepts/config/#configuration-on-typeadapter "Permanent link")

[Type adapters](https://docs.pydantic.dev/latest/concepts/type_adapter/) (using the [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) class) support configuration, by providing a `config` argument.

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter(list[str], config=ConfigDict(coerce_numbers_to_str=True))

print(ta.validate_python([1, 2]))
#> ['1', '2']
```

## Configuration on other supported types¶

If you are using [standard library dataclasses](https://docs.python.org/3/library/dataclasses.html#module-dataclasses) or [`TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict) classes, the configuration can be set in two ways:

- Using the `__pydantic_config__` class attribute:

```python
from dataclasses import dataclass

from pydantic import ConfigDict

@dataclass
class User:
    __pydantic_config__ = ConfigDict(strict=True)

    id: int
    name: str = 'John Doe'
```
- Using the [`with_config`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.with_config) decorator (this avoids static type checking errors with [`TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict)):

```python
from typing_extensions import TypedDict

from pydantic import ConfigDict, with_config

@with_config(ConfigDict(str_to_lower=True))
class Model(TypedDict):
    x: str
```

## Change behaviour globally¶

If you wish to change the behaviour of Pydantic globally, you can create your own custom parent class with a custom configuration, as the configuration is inherited:

```python
from pydantic import BaseModel, ConfigDict

class Parent(BaseModel):
    model_config = ConfigDict(extra='allow')

class Model(Parent):
    x: str

m = Model(x='foo', y='bar')
print(m.model_dump())
#> {'x': 'foo', 'y': 'bar'}
```

If you provide configuration to the subclasses, it will be *merged* with the parent configuration:

```python
from pydantic import BaseModel, ConfigDict

class Parent(BaseModel):
    model_config = ConfigDict(extra='allow', str_to_lower=False)

class Model(Parent):
    model_config = ConfigDict(str_to_lower=True)

    x: str

m = Model(x='FOO', y='bar')
print(m.model_dump())
#> {'x': 'foo', 'y': 'bar'}
print(Model.model_config)
#> {'extra': 'allow', 'str_to_lower': True}
```

Warning

If your model inherits from multiple bases, Pydantic currently *doesn't* follow the [MRO](https://docs.python.org/3/glossary.html#term-method-resolution-order). For more details, see [this issue](https://github.com/pydantic/pydantic/issues/9992).

## Configuration propagation¶

Note that when using types that support configuration as field annotations on other types, configuration will *not* be propagated. In the following example, each model has its own "configuration boundary":

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    name: str

class Parent(BaseModel):
    user: User

    model_config = ConfigDict(str_max_length=2)

print(Parent(user={'name': 'John Doe'}))
#> user=User(name='John Doe')
```
---
title: "Serialization - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/serialization/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
Beyond accessing model attributes directly via their field names (e.g. `model.foobar`), models can be converted, dumped, serialized, and exported in a number of ways.

Serialize versus dump

Pydantic uses the terms "serialize" and "dump" interchangeably. Both refer to the process of converting a model to a dictionary or JSON-encoded string.

Outside of Pydantic, the word "serialize" usually refers to converting in-memory data into a string or bytes. However, in the context of Pydantic, there is a very close relationship between converting an object from a more structured form — such as a Pydantic model, a dataclass, etc. — into a less structured form comprised of Python built-ins such as dict.

While we could (and on occasion, do) distinguish between these scenarios by using the word "dump" when converting to primitives and "serialize" when converting to string, for practical purposes, we frequently use the word "serialize" to refer to both of these situations, even though it does not always imply conversion to a string or bytes.

## `model.model_dump(...)` [¶](https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump "Permanent link")

API Documentation

[`pydantic.main.BaseModel.model_dump`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump)  

This is the primary way of converting a model to a dictionary. Sub-models will be recursively converted to dictionaries.

By default, the output may contain non-JSON-serializable Python objects. The `mode` argument can be specified as `'json'` to ensure that the output only contains JSON serializable types. Other parameters exist to include or exclude fields, [including nested fields](https://docs.pydantic.dev/latest/concepts/serialization/#advanced-include-and-exclude), or to further customize the serialization behaviour.

See the available [parameters](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump) for more information.

Note

The one exception to sub-models being converted to dictionaries is that [`RootModel`](https://docs.pydantic.dev/latest/concepts/models/#rootmodel-and-custom-root-types) and its subclasses will have the `root` field value dumped directly, without a wrapping dictionary. This is also done recursively.

Note

You can use [computed fields](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.computed_field) to include `property` and `cached_property` data in the `model.model_dump(...)` output.

Example:

```
from typing import Any, Optional

from pydantic import BaseModel, Field, Json

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    banana: Optional[float] = 1.1
    foo: str = Field(serialization_alias='foo_alias')
    bar: BarModel

m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(include={'foo', 'bar'}))
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(exclude={'foo', 'bar'}))
#> {'banana': 3.14}
print(m.model_dump(by_alias=True))
#> {'banana': 3.14, 'foo_alias': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(
        exclude_unset=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=1.1, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=None, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_none=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}

class Model(BaseModel):
    x: list[Json[Any]]

print(Model(x=['{"a": 1}', '[1, 2]']).model_dump())
#> {'x': [{'a': 1}, [1, 2]]}
print(Model(x=['{"a": 1}', '[1, 2]']).model_dump(round_trip=True))
#> {'x': ['{"a":1}', '[1,2]']}
```

```
from typing import Any

from pydantic import BaseModel, Field, Json

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    banana: float | None = 1.1
    foo: str = Field(serialization_alias='foo_alias')
    bar: BarModel

m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

# returns a dictionary:
print(m.model_dump())
#> {'banana': 3.14, 'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(include={'foo', 'bar'}))
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(m.model_dump(exclude={'foo', 'bar'}))
#> {'banana': 3.14}
print(m.model_dump(by_alias=True))
#> {'banana': 3.14, 'foo_alias': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(
        exclude_unset=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=1.1, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(foo='hello', bar={'whatever': 123}).model_dump(
        exclude_defaults=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}
print(
    FooBarModel(banana=None, foo='hello', bar={'whatever': 123}).model_dump(
        exclude_none=True
    )
)
#> {'foo': 'hello', 'bar': {'whatever': 123}}

class Model(BaseModel):
    x: list[Json[Any]]

print(Model(x=['{"a": 1}', '[1, 2]']).model_dump())
#> {'x': [{'a': 1}, [1, 2]]}
print(Model(x=['{"a": 1}', '[1, 2]']).model_dump(round_trip=True))
#> {'x': ['{"a":1}', '[1,2]']}
```

## `model.model_dump_json(...)` [¶](https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump_json "Permanent link")

API Documentation

[`pydantic.main.BaseModel.model_dump_json`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json)  

The `.model_dump_json()` method serializes a model directly to a JSON-encoded string that is equivalent to the result produced by [`.model_dump()`](https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump).

See the available [parameters](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json) for more information.

Note

Pydantic can serialize many commonly used types to JSON that would otherwise be incompatible with a simple `json.dumps(foobar)` (e.g. `datetime`, `date` or `UUID`) .

```python
from datetime import datetime

from pydantic import BaseModel

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    foo: datetime
    bar: BarModel

m = FooBarModel(foo=datetime(2032, 6, 1, 12, 13, 14), bar={'whatever': 123})
print(m.model_dump_json())
#> {"foo":"2032-06-01T12:13:14","bar":{"whatever":123}}
print(m.model_dump_json(indent=2))
"""
{
  "foo": "2032-06-01T12:13:14",
  "bar": {
    "whatever": 123
  }
}
"""
```

## `dict(model)` and iteration[¶](https://docs.pydantic.dev/latest/concepts/serialization/#dictmodel-and-iteration "Permanent link")

Pydantic models can also be converted to dictionaries using `dict(model)`, and you can also iterate over a model's fields using `for field_name, field_value in model:`. With this approach the raw field values are returned, so sub-models will not be converted to dictionaries.

Example:

```python
from pydantic import BaseModel

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel

m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

print(dict(m))
#> {'banana': 3.14, 'foo': 'hello', 'bar': BarModel(whatever=123)}
for name, value in m:
    print(f'{name}: {value}')
    #> banana: 3.14
    #> foo: hello
    #> bar: whatever=123
```

Note also that [`RootModel`](https://docs.pydantic.dev/latest/concepts/models/#rootmodel-and-custom-root-types) *does* get converted to a dictionary with the key `'root'`.

## Custom serializers¶

Pydantic provides several [functional serializers](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers) to customise how a model is serialized to a dictionary or JSON.

- [`@field_serializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.field_serializer)
- [`@model_serializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.model_serializer)
- [`PlainSerializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.PlainSerializer)
- [`WrapSerializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.WrapSerializer)

Serialization can be customised on a field using the [`@field_serializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.field_serializer) decorator, and on a model using the [`@model_serializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.model_serializer) decorator.

```python
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer, model_serializer

class WithCustomEncoders(BaseModel):
    model_config = ConfigDict(ser_json_timedelta='iso8601')

    dt: datetime
    diff: timedelta

    @field_serializer('dt')
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()

m = WithCustomEncoders(
    dt=datetime(2032, 6, 1, tzinfo=timezone.utc), diff=timedelta(hours=100)
)
print(m.model_dump_json())
#> {"dt":1969660800.0,"diff":"P4DT4H"}

class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> dict[str, Any]:
        return {'x': f'serialized {self.x}'}

print(Model(x='test value').model_dump_json())
#> {"x":"serialized test value"}
```

Note

A single serializer can also be called on all fields by passing the special value '\*' to the [`@field_serializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.field_serializer) decorator.

In addition, [`PlainSerializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.PlainSerializer) and [`WrapSerializer`](https://docs.pydantic.dev/latest/api/functional_serializers/#pydantic.functional_serializers.WrapSerializer) enable you to use a function to modify the output of serialization.

Both serializers accept optional arguments including:

- `return_type` specifies the return type for the function. If omitted it will be inferred from the type annotation.
- `when_used` specifies when this serializer should be used. Accepts a string with values 'always', 'unless-none', 'json', and 'json-unless-none'. Defaults to 'always'.

`PlainSerializer` uses a simple function to modify the output of serialization.

```python
from typing import Annotated

from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer

FancyInt = Annotated[
    int, PlainSerializer(lambda x: f'{x:,}', return_type=str, when_used='json')
]

class MyModel(BaseModel):
    x: FancyInt

print(MyModel(x=1234).model_dump())
#> {'x': 1234}

print(MyModel(x=1234).model_dump(mode='json'))
#> {'x': '1,234'}
```

`WrapSerializer` receives the raw inputs along with a handler function that applies the standard serialization logic, and can modify the resulting value before returning it as the final output of serialization.

```python
from typing import Annotated, Any

from pydantic import BaseModel, SerializerFunctionWrapHandler
from pydantic.functional_serializers import WrapSerializer

def ser_wrap(v: Any, nxt: SerializerFunctionWrapHandler) -> str:
    return f'{nxt(v + 1):,}'

FancyInt = Annotated[int, WrapSerializer(ser_wrap, when_used='json')]

class MyModel(BaseModel):
    x: FancyInt

print(MyModel(x=1234).model_dump())
#> {'x': 1234}

print(MyModel(x=1234).model_dump(mode='json'))
#> {'x': '1,235'}
```

### Overriding the return type when dumping a model¶

While the return value of `.model_dump()` can usually be described as `dict[str, Any]`, through the use of `@model_serializer` you can actually cause it to return a value that doesn't match this signature:

```python
from pydantic import BaseModel, model_serializer

class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> str:
        return self.x

print(Model(x='not a dict').model_dump())
#> not a dict
```

If you want to do this and still get proper type-checking for this method, you can override `.model_dump()` in an `if TYPE_CHECKING:` block:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, model_serializer

class Model(BaseModel):
    x: str

    @model_serializer
    def ser_model(self) -> str:
        return self.x

    if TYPE_CHECKING:
        # Ensure type checkers see the correct return type
        def model_dump(
            self,
            *,
            mode: Literal['json', 'python'] | str = 'python',
            include: Any = None,
            exclude: Any = None,
            by_alias: bool | None = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool = True,
        ) -> str: ...
```

This trick is actually used in [`RootModel`](https://docs.pydantic.dev/latest/concepts/models/#rootmodel-and-custom-root-types) for precisely this purpose.

## Serializing subclasses¶
### Subclasses of standard types¶

Subclasses of standard types are automatically dumped like their super-classes:

```python
from datetime import date, timedelta
from typing import Any

from pydantic_core import core_schema

from pydantic import BaseModel, GetCoreSchemaHandler

class DayThisYear(date):
    """
    Contrived example of a special type of date that
    takes an int and interprets it as a day in the current year
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.int_schema(),
            serialization=core_schema.format_ser_schema('%Y-%m-%d'),
        )

    @classmethod
    def validate(cls, v: int):
        return date(2023, 1, 1) + timedelta(days=v)

class FooModel(BaseModel):
    date: DayThisYear

m = FooModel(date=300)
print(m.model_dump_json())
#> {"date":"2023-10-28"}
```

### Subclass instances for fields of `BaseModel`, dataclasses, `TypedDict`[¶](https://docs.pydantic.dev/latest/concepts/serialization/#subclass-instances-for-fields-of-basemodel-dataclasses-typeddict "Permanent link")

When using fields whose annotations are themselves struct-like types (e.g., `BaseModel` subclasses, dataclasses, etc.), the default behavior is to serialize the attribute value as though it was an instance of the annotated type, even if it is a subclass. More specifically, only the fields from the *annotated* type will be included in the dumped object:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str

class UserLogin(User):
    password: str

class OuterModel(BaseModel):
    user: User

user = UserLogin(name='pydantic', password='hunter2')

m = OuterModel(user=user)
print(m)
#> user=UserLogin(name='pydantic', password='hunter2')
print(m.model_dump())  # note: the password field is not included
#> {'user': {'name': 'pydantic'}}
```

Migration Warning

This behavior is different from how things worked in Pydantic V1, where we would always include all (subclass) fields when recursively dumping models to dicts. The motivation behind this change in behavior is that it helps ensure that you know precisely which fields could be included when serializing, even if subclasses get passed when instantiating the object. In particular, this can help prevent surprises when adding sensitive information like secrets as fields of subclasses.

### Serializing with duck-typing 🦆¶

What is serialization with duck typing?

Duck-typing serialization is the behavior of serializing an object based on the fields present in the object itself, rather than the fields present in the schema of the object. This means that when an object is serialized, fields present in a subclass, but not in the original schema, will be included in the serialized output.

This behavior was the default in Pydantic V1, but was changed in V2 to help ensure that you know precisely which fields would be included when serializing, even if subclasses get passed when instantiating the object. This helps prevent security risks when serializing subclasses with sensitive information, for example.

If you want v1-style duck-typing serialization behavior, you can use a runtime setting, or annotate individual types.

- Field / type level: use the `SerializeAsAny` annotation
- Runtime level: use the `serialize_as_any` flag when calling `model_dump()` or `model_dump_json()`

We discuss these options below in more detail:

#### `SerializeAsAny` annotation:[¶](https://docs.pydantic.dev/latest/concepts/serialization/#serializeasany-annotation "Permanent link")

If you want duck-typing serialization behavior, this can be done using the `SerializeAsAny` annotation on a type:

```python
from pydantic import BaseModel, SerializeAsAny

class User(BaseModel):
    name: str

class UserLogin(User):
    password: str

class OuterModel(BaseModel):
    as_any: SerializeAsAny[User]
    as_user: User

user = UserLogin(name='pydantic', password='password')

print(OuterModel(as_any=user, as_user=user).model_dump())
"""
{
    'as_any': {'name': 'pydantic', 'password': 'password'},
    'as_user': {'name': 'pydantic'},
}
"""
```

When a field is annotated as `SerializeAsAny[<SomeType>]`, the validation behavior will be the same as if it was annotated as `<SomeType>`, and type-checkers like mypy will treat the attribute as having the appropriate type as well. But when serializing, the field will be serialized as though the type hint for the field was `Any`, which is where the name comes from.

#### `serialize_as_any` runtime setting[¶](https://docs.pydantic.dev/latest/concepts/serialization/#serialize_as_any-runtime-setting "Permanent link")

The `serialize_as_any` runtime setting can be used to serialize model data with or without duck typed serialization behavior. `serialize_as_any` can be passed as a keyword argument to the `model_dump()` and `model_dump_json` methods of `BaseModel`s and `RootModel`s. It can also be passed as a keyword argument to the `dump_python()` and `dump_json()` methods of `TypeAdapter`s.

If `serialize_as_any` is set to `True`, the model will be serialized using duck typed serialization behavior, which means that the model will ignore the schema and instead ask the object itself how it should be serialized. In particular, this means that when model subclasses are serialized, fields present in the subclass but not in the original schema will be included.

If `serialize_as_any` is set to `False` (which is the default), the model will be serialized using the schema, which means that fields present in a subclass but not in the original schema will be ignored.

Why is this flag useful?

Sometimes, you want to make sure that no matter what fields might have been added in subclasses, the serialized object will only have the fields listed in the original type definition. This can be useful if you add something like a `password: str` field in a subclass that you don't want to accidentally include in the serialized output.

For example:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str

class UserLogin(User):
    password: str

class OuterModel(BaseModel):
    user1: User
    user2: User

user = UserLogin(name='pydantic', password='password')

outer_model = OuterModel(user1=user, user2=user)
print(outer_model.model_dump(serialize_as_any=True))  
"""
{
    'user1': {'name': 'pydantic', 'password': 'password'},
    'user2': {'name': 'pydantic', 'password': 'password'},
}
"""

print(outer_model.model_dump(serialize_as_any=False))  
#> {'user1': {'name': 'pydantic'}, 'user2': {'name': 'pydantic'}}
```

This setting even takes effect with nested and recursive patterns as well. For example:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    friends: list['User']

class UserLogin(User):
    password: str

class OuterModel(BaseModel):
    user: User

user = UserLogin(
    name='samuel',
    password='pydantic-pw',
    friends=[UserLogin(name='sebastian', password='fastapi-pw', friends=[])],
)

print(OuterModel(user=user).model_dump(serialize_as_any=True))  
"""
{
    'user': {
        'name': 'samuel',
        'friends': [
            {'name': 'sebastian', 'friends': [], 'password': 'fastapi-pw'}
        ],
        'password': 'pydantic-pw',
    }
}
"""

print(OuterModel(user=user).model_dump(serialize_as_any=False))  
"""
{'user': {'name': 'samuel', 'friends': [{'name': 'sebastian', 'friends': []}]}}
"""
```

Note

The behavior of the `serialize_as_any` runtime flag is almost the same as the behavior of the `SerializeAsAny` annotation. There are a few nuanced differences that we're working to resolve, but for the most part, you can expect the same behavior from both. See more about the differences in this [active issue](https://github.com/pydantic/pydantic/issues/9049)

#### Overriding the `serialize_as_any` default (False)[¶](https://docs.pydantic.dev/latest/concepts/serialization/#overriding-the-serialize_as_any-default-false "Permanent link")

You can override the default setting for `serialize_as_any` by configuring a subclass of `BaseModel` that overrides the default for the `serialize_as_any` parameter to `model_dump()` and `model_dump_json()`, and then use that as the base class (instead of `pydantic.BaseModel`) for any model you want to have this default behavior.

For example, you could do the following if you want to use duck-typing serialization by default:

```python
from typing import Any

from pydantic import BaseModel, SecretStr

class MyBaseModel(BaseModel):
    def model_dump(self, **kwargs) -> dict[str, Any]:
        return super().model_dump(serialize_as_any=True, **kwargs)

    def model_dump_json(self, **kwargs) -> str:
        return super().model_dump_json(serialize_as_any=True, **kwargs)

class User(MyBaseModel):
    name: str

class UserInfo(User):
    password: SecretStr

class OuterModel(MyBaseModel):
    user: User

u = OuterModel(user=UserInfo(name='John', password='secret_pw'))
print(u.model_dump_json())  
#> {"user":{"name":"John","password":"**********"}}
```

## `pickle.dumps(model)`[¶](https://docs.pydantic.dev/latest/concepts/serialization/#pickledumpsmodel "Permanent link")

Pydantic models support efficient pickling and unpickling.

```python
import pickle

from pydantic import BaseModel

class FooBarModel(BaseModel):
    a: str
    b: int

m = FooBarModel(a='hello', b=123)
print(m)
#> a='hello' b=123
data = pickle.dumps(m)
print(data[:20])
#> b'\x80\x04\x95\x95\x00\x00\x00\x00\x00\x00\x00\x8c\x08__main_'
m2 = pickle.loads(data)
print(m2)
#> a='hello' b=123
```

## Advanced include and exclude¶

The `model_dump` and `model_dump_json` methods support `include` and `exclude` parameters which can either be sets or dictionaries. This allows nested selection of which fields to export:

```python
from pydantic import BaseModel, SecretStr

class User(BaseModel):
    id: int
    username: str
    password: SecretStr

class Transaction(BaseModel):
    id: str
    user: User
    value: int

t = Transaction(
    id='1234567890',
    user=User(id=42, username='JohnDoe', password='hashedpassword'),
    value=9876543210,
)

# using a set:
print(t.model_dump(exclude={'user', 'value'}))
#> {'id': '1234567890'}

# using a dict:
print(t.model_dump(exclude={'user': {'username', 'password'}, 'value': True}))
#> {'id': '1234567890', 'user': {'id': 42}}

print(t.model_dump(include={'id': True, 'user': {'id'}}))
#> {'id': '1234567890', 'user': {'id': 42}}
```

Using `True` indicates that we want to exclude or include an entire key, just as if we included it in a set (note that using `False` isn't supported). This can be done at any depth level.

Special care must be taken when including or excluding fields from a list or tuple of submodels or dictionaries. In this scenario, `model_dump` and related methods expect integer keys for element-wise inclusion or exclusion. To exclude a field from **every** member of a list or tuple, the dictionary key `'__all__'` can be used, as shown here:

```python
import datetime

from pydantic import BaseModel, SecretStr

class Country(BaseModel):
    name: str
    phone_code: int

class Address(BaseModel):
    post_code: int
    country: Country

class CardDetails(BaseModel):
    number: SecretStr
    expires: datetime.date

class Hobby(BaseModel):
    name: str
    info: str

class User(BaseModel):
    first_name: str
    second_name: str
    address: Address
    card_details: CardDetails
    hobbies: list[Hobby]

user = User(
    first_name='John',
    second_name='Doe',
    address=Address(
        post_code=123456, country=Country(name='USA', phone_code=1)
    ),
    card_details=CardDetails(
        number='4212934504460000', expires=datetime.date(2020, 5, 1)
    ),
    hobbies=[
        Hobby(name='Programming', info='Writing code and stuff'),
        Hobby(name='Gaming', info='Hell Yeah!!!'),
    ],
)

exclude_keys = {
    'second_name': True,
    'address': {'post_code': True, 'country': {'phone_code'}},
    'card_details': True,
    # You can exclude fields from specific members of a tuple/list by index:
    'hobbies': {-1: {'info'}},
}

include_keys = {
    'first_name': True,
    'address': {'country': {'name'}},
    'hobbies': {0: True, -1: {'name'}},
}

# would be the same as user.model_dump(exclude=exclude_keys) in this case:
print(user.model_dump(include=include_keys))
"""
{
    'first_name': 'John',
    'address': {'country': {'name': 'USA'}},
    'hobbies': [
        {'name': 'Programming', 'info': 'Writing code and stuff'},
        {'name': 'Gaming'},
    ],
}
"""

# To exclude a field from all members of a nested list or tuple, use "__all__":
print(user.model_dump(exclude={'hobbies': {'__all__': {'info'}}}))
"""
{
    'first_name': 'John',
    'second_name': 'Doe',
    'address': {
        'post_code': 123456,
        'country': {'name': 'USA', 'phone_code': 1},
    },
    'card_details': {
        'number': SecretStr('**********'),
        'expires': datetime.date(2020, 5, 1),
    },
    'hobbies': [{'name': 'Programming'}, {'name': 'Gaming'}],
}
"""
```

The same holds for the `model_dump_json` method.

### Model- and field-level include and exclude¶

In addition to the explicit `exclude` and `include` arguments passed to `model_dump` and `model_dump_json` methods, we can also pass the `exclude: bool` arguments directly to the `Field` constructor:

Setting `exclude` on the field constructor (`Field(exclude=True)`) takes priority over the `exclude`/`include` on `model_dump` and `model_dump_json`:

```python
from pydantic import BaseModel, Field, SecretStr

class User(BaseModel):
    id: int
    username: str
    password: SecretStr = Field(exclude=True)

class Transaction(BaseModel):
    id: str
    value: int = Field(exclude=True)

t = Transaction(
    id='1234567890',
    value=9876543210,
)

print(t.model_dump())
#> {'id': '1234567890'}
print(t.model_dump(include={'id': True, 'value': True}))  
#> {'id': '1234567890'}
```

That being said, setting `exclude` on the field constructor (`Field(exclude=True)`) does not take priority over the `exclude_unset`, `exclude_none`, and `exclude_default` parameters on `model_dump` and `model_dump_json`:

```
from typing import Optional

from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str
    age: Optional[int] = Field(None, exclude=False)

person = Person(name='Jeremy')

print(person.model_dump())
#> {'name': 'Jeremy', 'age': None}
print(person.model_dump(exclude_none=True))  
#> {'name': 'Jeremy'}
print(person.model_dump(exclude_unset=True))  
#> {'name': 'Jeremy'}
print(person.model_dump(exclude_defaults=True))  
#> {'name': 'Jeremy'}
```

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str
    age: int | None = Field(None, exclude=False)

person = Person(name='Jeremy')

print(person.model_dump())
#> {'name': 'Jeremy', 'age': None}
print(person.model_dump(exclude_none=True))  
#> {'name': 'Jeremy'}
print(person.model_dump(exclude_unset=True))  
#> {'name': 'Jeremy'}
print(person.model_dump(exclude_defaults=True))  
#> {'name': 'Jeremy'}
```

1. `age` excluded from the output because `exclude_none` was set to `True`, and `age` is `None`.
2. `age` excluded from the output because `exclude_unset` was set to `True`, and `age` was not set in the Person constructor.
3. `age` excluded from the output because `exclude_defaults` was set to `True`, and `age` takes the default value of `None`.

## Serialization Context¶

You can pass a context object to the serialization methods which can be accessed from the `info` parameter to decorated serializer functions. This is useful when you need to dynamically update the serialization behavior during runtime. For example, if you wanted a field to be dumped depending on a dynamically controllable set of allowed values, this could be done by passing the allowed values by context:

```python
from pydantic import BaseModel, SerializationInfo, field_serializer

class Model(BaseModel):
    text: str

    @field_serializer('text')
    def remove_stopwords(self, v: str, info: SerializationInfo):
        context = info.context
        if context:
            stopwords = context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v

model = Model.model_construct(**{'text': 'This is an example document'})
print(model.model_dump())  # no context
#> {'text': 'This is an example document'}
print(model.model_dump(context={'stopwords': ['this', 'is', 'an']}))
#> {'text': 'example document'}
print(model.model_dump(context={'stopwords': ['document']}))
#> {'text': 'This is an example'}
```

Similarly, you can [use a context for validation](https://docs.pydantic.dev/latest/concepts/validators/#validation-context).

## `model_copy(...)` [¶](https://docs.pydantic.dev/latest/concepts/serialization/#model_copy "Permanent link")

API Documentation

[`pydantic.main.BaseModel.model_copy`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_copy)  

`model_copy()` allows models to be duplicated (with optional updates), which is particularly useful when working with frozen models.

Example:

```python
from pydantic import BaseModel

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    banana: float
    foo: str
    bar: BarModel

m = FooBarModel(banana=3.14, foo='hello', bar={'whatever': 123})

print(m.model_copy(update={'banana': 0}))
#> banana=0 foo='hello' bar=BarModel(whatever=123)
print(id(m.bar) == id(m.model_copy().bar))
#> True
# normal copy gives the same object reference for bar
print(id(m.bar) == id(m.model_copy(deep=True).bar))
#> False
# deep copy gives a new object reference for \`bar\`
```
---
title: "Validators - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/validators/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
In addition to Pydantic's [built-in validation capabilities](https://docs.pydantic.dev/latest/concepts/fields/#field-constraints), you can leverage custom validators at the field and model levels to enforce more complex constraints and ensure the integrity of your data.

Tip

Want to quickly jump to the relevant validator section?

- Field validators

---

- [field *after* validators](https://docs.pydantic.dev/latest/concepts/validators/#field-after-validator)
- [field *before* validators](https://docs.pydantic.dev/latest/concepts/validators/#field-before-validator)
- [field *plain* validators](https://docs.pydantic.dev/latest/concepts/validators/#field-plain-validator)
- [field *wrap* validators](https://docs.pydantic.dev/latest/concepts/validators/#field-wrap-validator)
- Model validators

---

- [model *before* validators](https://docs.pydantic.dev/latest/concepts/validators/#model-before-validator)
- [model *after* validators](https://docs.pydantic.dev/latest/concepts/validators/#model-after-validator)
- [model *wrap* validators](https://docs.pydantic.dev/latest/concepts/validators/#model-wrap-validator)

## Field validators¶
API Documentation

[`pydantic.functional_validators.WrapValidator`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.WrapValidator)  
[`pydantic.functional_validators.PlainValidator`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.PlainValidator)  
[`pydantic.functional_validators.BeforeValidator`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.BeforeValidator)  
[`pydantic.functional_validators.AfterValidator`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.AfterValidator)  
[`pydantic.functional_validators.field_validator`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.field_validator)  

In its simplest form, a field validator is a callable taking the value to be validated as an argument and **returning the validated value**. The callable can perform checks for specific conditions (see [raising validation errors](https://docs.pydantic.dev/latest/concepts/validators/#raising-validation-errors)) and make changes to the validated value (coercion or mutation).

**Four** different types of validators can be used. They can all be defined using the [annotated pattern](https://docs.pydantic.dev/latest/concepts/fields/#the-annotated-pattern) or using the [`field_validator()`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.field_validator) decorator, applied on a [class method](https://docs.python.org/3/library/functions.html#classmethod):

- ***After* validators**: run after Pydantic's internal validation. They are generally more type safe and thus easier to implement.

Here is an example of a validator performing a validation check, and returning the value unchanged.

```python
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ValidationError

def is_even(value: int) -> int:
    if value % 2 == 1:
        raise ValueError(f'{value} is not an even number')
    return value  

class Model(BaseModel):
    number: Annotated[int, AfterValidator(is_even)]

try:
    Model(number=1)
except ValidationError as err:
    print(err)
    """
    1 validation error for Model
    number
      Value error, 1 is not an even number [type=value_error, input_value=1, input_type=int]
    """
```

Here is an example of a validator performing a validation check, and returning the value unchanged, this time using the [`field_validator()`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.field_validator) decorator.

```python
from pydantic import BaseModel, ValidationError, field_validator

class Model(BaseModel):
    number: int

    @field_validator('number', mode='after')  
    @classmethod
    def is_even(cls, value: int) -> int:
        if value % 2 == 1:
            raise ValueError(f'{value} is not an even number')
        return value  

try:
    Model(number=1)
except ValidationError as err:
    print(err)
    """
    1 validation error for Model
    number
      Value error, 1 is not an even number [type=value_error, input_value=1, input_type=int]
    """
```

1. `'after'` is the default mode for the decorator, and can be omitted.
2. Note that it is important to return the validated value.

Example mutating the value

Here is an example of a validator making changes to the validated value (no exception is raised).

```
from typing import Annotated

from pydantic import AfterValidator, BaseModel

def double_number(value: int) -> int:
    return value * 2

class Model(BaseModel):
    number: Annotated[int, AfterValidator(double_number)]

print(Model(number=2))
#> number=4
```

```python
from pydantic import BaseModel, field_validator

class Model(BaseModel):
    number: int

    @field_validator('number', mode='after')  
    @classmethod
    def double_number(cls, value: int) -> int:
        return value * 2

print(Model(number=2))
#> number=4
```

1. `'after'` is the default mode for the decorator, and can be omitted.

- ***Before* validators**: run before Pydantic's internal parsing and validation (e.g. coercion of a `str` to an `int`). These are more flexible than [*after* validators](https://docs.pydantic.dev/latest/concepts/validators/#field-after-validator), but they also have to deal with the raw input, which in theory could be any arbitrary object. You should also avoid mutating the value directly if you are raising a [validation error](https://docs.pydantic.dev/latest/concepts/validators/#raising-validation-errors) later in your validator function, as the mutated value may be passed to other validators if using [unions](https://docs.pydantic.dev/latest/concepts/unions/).

The value returned from this callable is then validated against the provided type annotation by Pydantic.

```
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ValidationError

def ensure_list(value: Any) -> Any:  
    if not isinstance(value, list):  
        return [value]
    else:
        return value

class Model(BaseModel):
    numbers: Annotated[list[int], BeforeValidator(ensure_list)]

print(Model(numbers=2))
#> numbers=[2]
try:
    Model(numbers='str')
except ValidationError as err:
    print(err)  
    """
    1 validation error for Model
    numbers.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='str', input_type=str]
    """
```

```python
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

class Model(BaseModel):
    numbers: list[int]

    @field_validator('numbers', mode='before')
    @classmethod
    def ensure_list(cls, value: Any) -> Any:  
        if not isinstance(value, list):  
            return [value]
        else:
            return value

print(Model(numbers=2))
#> numbers=[2]
try:
    Model(numbers='str')
except ValidationError as err:
    print(err)  
    """
    1 validation error for Model
    numbers.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='str', input_type=str]
    """
```

1. Notice the use of [`Any`](https://docs.python.org/3/library/typing.html#typing.Any) as a type hint for `value`. *Before* validators take the raw input, which can be anything.
2. Note that you might want to check for other sequence types (such as tuples) that would normally successfully validate against the `list` type. *Before* validators give you more flexibility, but you have to account for every possible case.
3. Pydantic still performs validation against the `int` type, no matter if our `ensure_list` validator did operations on the original input type.

- ***Plain* validators**: act similarly to *before* validators but they **terminate validation immediately** after returning, so no further validators are called and Pydantic does not do any of its internal validation against the field type.

```
from typing import Annotated, Any

from pydantic import BaseModel, PlainValidator

def val_number(value: Any) -> Any:
    if isinstance(value, int):
        return value * 2
    else:
        return value

class Model(BaseModel):
    number: Annotated[int, PlainValidator(val_number)]

print(Model(number=4))
#> number=8
print(Model(number='invalid'))  
#> number='invalid'
```

```python
from typing import Any

from pydantic import BaseModel, field_validator

class Model(BaseModel):
    number: int

    @field_validator('number', mode='plain')
    @classmethod
    def val_number(cls, value: Any) -> Any:
        if isinstance(value, int):
            return value * 2
        else:
            return value

print(Model(number=4))
#> number=8
print(Model(number='invalid'))  
#> number='invalid'
```

1. Although `'invalid'` shouldn't validate against the `int` type, Pydantic accepts the input.

- ***Wrap* validators**: are the most flexible of all. You can run code before or after Pydantic and other validators process the input, or you can terminate validation immediately, either by returning the value early or by raising an error.

Such validators must be defined with a **mandatory** extra `handler` parameter: a callable taking the value to be validated as an argument. Internally, this handler will delegate validation of the value to Pydantic. You are free to wrap the call to the handler in a [`try..except`](https://docs.python.org/3/tutorial/errors.html#handling-exceptions) block, or not call it at all.

```
from typing import Any

from typing import Annotated

from pydantic import BaseModel, Field, ValidationError, ValidatorFunctionWrapHandler, WrapValidator

def truncate(value: Any, handler: ValidatorFunctionWrapHandler) -> str:
    try:
        return handler(value)
    except ValidationError as err:
        if err.errors()[0]['type'] == 'string_too_long':
            return handler(value[:5])
        else:
            raise

class Model(BaseModel):
    my_string: Annotated[str, Field(max_length=5), WrapValidator(truncate)]

print(Model(my_string='abcde'))
#> my_string='abcde'
print(Model(my_string='abcdef'))
#> my_string='abcde'
```

```
from typing import Any

from typing import Annotated

from pydantic import BaseModel, Field, ValidationError, ValidatorFunctionWrapHandler, field_validator

class Model(BaseModel):
    my_string: Annotated[str, Field(max_length=5)]

    @field_validator('my_string', mode='wrap')
    @classmethod
    def truncate(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> str:
        try:
            return handler(value)
        except ValidationError as err:
            if err.errors()[0]['type'] == 'string_too_long':
                return handler(value[:5])
            else:
                raise

print(Model(my_string='abcde'))
#> my_string='abcde'
print(Model(my_string='abcdef'))
#> my_string='abcde'
```

Validation of default values

As mentioned in the [fields documentation](https://docs.pydantic.dev/latest/concepts/fields/#validate-default-values), default values of fields are *not* validated unless configured to do so, and thus custom validators will not be applied as well.

### Which validator pattern to use¶

While both approaches can achieve the same thing, each pattern provides different benefits.

#### Using the annotated pattern¶

One of the key benefits of using the [annotated pattern](https://docs.pydantic.dev/latest/concepts/fields/#the-annotated-pattern) is to make validators reusable:

```python
from typing import Annotated

from pydantic import AfterValidator, BaseModel

def is_even(value: int) -> int:
    if value % 2 == 1:
        raise ValueError(f'{value} is not an even number')
    return value

EvenNumber = Annotated[int, AfterValidator(is_even)]

class Model1(BaseModel):
    my_number: EvenNumber

class Model2(BaseModel):
    other_number: Annotated[EvenNumber, AfterValidator(lambda v: v + 2)]

class Model3(BaseModel):
    list_of_even_numbers: list[EvenNumber]  
```

It is also easier to understand which validators are applied to a type, by just looking at the field annotation.

#### Using the decorator pattern¶

One of the key benefits of using the [`field_validator()`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.field_validator) decorator is to apply the function to multiple fields:

```python
from pydantic import BaseModel, field_validator

class Model(BaseModel):
    f1: str
    f2: str

    @field_validator('f1', 'f2', mode='before')
    @classmethod
    def capitalize(cls, value: str) -> str:
        return value.capitalize()
```

Here are a couple additional notes about the decorator usage:

- If you want the validator to apply to all fields (including the ones defined in subclasses), you can pass `'*'` as the field name argument.
- By default, the decorator will ensure the provided field name(s) are defined on the model. If you want to disable this check during class creation, you can do so by passing `False` to the `check_fields` argument. This is useful when the field validator is defined on a base class, and the field is expected to be set on subclasses.

## Model validators¶
API Documentation

[`pydantic.functional_validators.model_validator`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.model_validator)  

Validation can also be performed on the entire model's data using the [`model_validator()`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.model_validator) decorator.

**Three** different types of model validators can be used:

- ***After* validators**: run after the whole model has been validated. As such, they are defined as *instance* methods and can be seen as post-initialization hooks. Important note: the validated instance should be returned.

```python
from typing_extensions import Self

from pydantic import BaseModel, model_validator

class UserModel(BaseModel):
    username: str
    password: str
    password_repeat: str

    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError('Passwords do not match')
        return self
```

- ***Before* validators**: are run before the model is instantiated. These are more flexible than *after* validators, but they also have to deal with the raw input, which in theory could be any arbitrary object. You should also avoid mutating the value directly if you are raising a [validation error](https://docs.pydantic.dev/latest/concepts/validators/#raising-validation-errors) later in your validator function, as the mutated value may be passed to other validators if using [unions](https://docs.pydantic.dev/latest/concepts/unions/).

```python
from typing import Any

from pydantic import BaseModel, model_validator

class UserModel(BaseModel):
    username: str

    @model_validator(mode='before')
    @classmethod
    def check_card_number_not_present(cls, data: Any) -> Any:  
        if isinstance(data, dict):  
            if 'card_number' in data:
                raise ValueError("'card_number' should not be included")
        return data
```

- ***Wrap* validators**: are the most flexible of all. You can run code before or after Pydantic and other validators process the input data, or you can terminate validation immediately, either by returning the data early or by raising an error.

```python
import logging
from typing import Any

from typing_extensions import Self

from pydantic import BaseModel, ModelWrapValidatorHandler, ValidationError, model_validator

class UserModel(BaseModel):
    username: str

    @model_validator(mode='wrap')
    @classmethod
    def log_failed_validation(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        try:
            return handler(data)
        except ValidationError:
            logging.error('Model %s failed to validate with data %s', cls, data)
            raise
```

On inheritance

A model validator defined in a base class will be called during the validation of a subclass instance.

Overriding a model validator in a subclass will override the base class' validator, and thus only the subclass' version of said validator will be called.

## Raising validation errors¶

To raise a validation error, three types of exceptions can be used:

- [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError): this is the most common exception raised inside validators.
- [`AssertionError`](https://docs.python.org/3/library/exceptions.html#AssertionError): using the [assert](https://docs.python.org/3/reference/simple_stmts.html#assert) statement also works, but be aware that these statements are skipped when Python is run with the [\-O](https://docs.python.org/3/using/cmdline.html#cmdoption-O) optimization flag.
- [`PydanticCustomError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.PydanticCustomError): a bit more verbose, but provides extra flexibility:

```python
from pydantic_core import PydanticCustomError

from pydantic import BaseModel, ValidationError, field_validator

class Model(BaseModel):
    x: int

    @field_validator('x', mode='after')
    @classmethod
    def validate_x(cls, v: int) -> int:
        if v % 42 == 0:
            raise PydanticCustomError(
                'the_answer_error',
                '{number} is the answer!',
                {'number': v},
            )
        return v

try:
    Model(x=42 * 2)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      84 is the answer! [type=the_answer_error, input_value=84, input_type=int]
    """
```

## Validation info¶

Both the field and model validators callables (in all modes) can optionally take an extra [`ValidationInfo`](https://docs.pydantic.dev/latest/api/pydantic_core_schema/#pydantic_core.core_schema.ValidationInfo) argument, providing useful extra information, such as:

- [already validated data](https://docs.pydantic.dev/latest/concepts/validators/#validation-data)
- [user defined context](https://docs.pydantic.dev/latest/concepts/validators/#validation-context)
- the current validation mode: either `'python'` or `'json'` (see the [`mode`](https://docs.pydantic.dev/latest/api/pydantic_core_schema/#pydantic_core.core_schema.ValidationInfo.mode) property)
- the current field name (see the [`field_name`](https://docs.pydantic.dev/latest/api/pydantic_core_schema/#pydantic_core.core_schema.ValidationInfo.field_name) property).

### Validation data¶

For field validators, the already validated data can be accessed using the [`data`](https://docs.pydantic.dev/latest/api/pydantic_core_schema/#pydantic_core.core_schema.ValidationInfo.data) property. Here is an example than can be used as an alternative to the [*after* model validator](https://docs.pydantic.dev/latest/concepts/validators/#model-after-validator) example:

```python
from pydantic import BaseModel, ValidationInfo, field_validator

class UserModel(BaseModel):
    password: str
    password_repeat: str
    username: str

    @field_validator('password_repeat', mode='after')
    @classmethod
    def check_passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data['password']:
            raise ValueError('Passwords do not match')
        return value
```

Warning

As validation is performed in the [order fields are defined](https://docs.pydantic.dev/latest/concepts/models/#field-ordering), you have to make sure you are not accessing a field that hasn't been validated yet. In the code above, for example, the `username` validated value is not available yet, as it is defined *after* `password_repeat`.

The [`data`](https://docs.pydantic.dev/latest/api/pydantic_core_schema/#pydantic_core.core_schema.ValidationInfo.data) property is `None` for [model validators](https://docs.pydantic.dev/latest/concepts/validators/#model-validators).

### Validation context¶

You can pass a context object to the [validation methods](https://docs.pydantic.dev/latest/concepts/models/#validating-data), which can be accessed inside the validator functions using the [`context`](https://docs.pydantic.dev/latest/api/pydantic_core_schema/#pydantic_core.core_schema.ValidationInfo.context) property:

```python
from pydantic import BaseModel, ValidationInfo, field_validator

class Model(BaseModel):
    text: str

    @field_validator('text', mode='after')
    @classmethod
    def remove_stopwords(cls, v: str, info: ValidationInfo) -> str:
        if isinstance(info.context, dict):
            stopwords = info.context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v

data = {'text': 'This is an example document'}
print(Model.model_validate(data))  # no context
#> text='This is an example document'
print(Model.model_validate(data, context={'stopwords': ['this', 'is', 'an']}))
#> text='example document'
```

Similarly, you can [use a context for serialization](https://docs.pydantic.dev/latest/concepts/serialization/#serialization-context).

Providing context when directly instantiating a model

It is currently not possible to provide a context when directly instantiating a model (i.e. when calling `Model(...)`). You can work around this through the use of a [`ContextVar`](https://docs.python.org/3/library/contextvars.html#contextvars.ContextVar) and a custom `__init__` method:

```python
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator

from pydantic import BaseModel, ValidationInfo, field_validator

_init_context_var = ContextVar('_init_context_var', default=None)

@contextmanager
def init_context(value: dict[str, Any]) -> Generator[None]:
    token = _init_context_var.set(value)
    try:
        yield
    finally:
        _init_context_var.reset(token)

class Model(BaseModel):
    my_number: int

    def __init__(self, /, **data: Any) -> None:
        self.__pydantic_validator__.validate_python(
            data,
            self_instance=self,
            context=_init_context_var.get(),
        )

    @field_validator('my_number')
    @classmethod
    def multiply_with_context(cls, value: int, info: ValidationInfo) -> int:
        if isinstance(info.context, dict):
            multiplier = info.context.get('multiplier', 1)
            value = value * multiplier
        return value

print(Model(my_number=2))
#> my_number=2

with init_context({'multiplier': 3}):
    print(Model(my_number=2))
    #> my_number=6

print(Model(my_number=2))
#> my_number=2
```
## Ordering of validators¶

When using the [annotated pattern](https://docs.pydantic.dev/latest/concepts/validators/#using-the-annotated-pattern), the order in which validators are applied is defined as follows: [*before*](https://docs.pydantic.dev/latest/concepts/validators/#field-before-validator) and [*wrap*](https://docs.pydantic.dev/latest/concepts/validators/#field-wrap-validator) validators are run from right to left, and [*after*](https://docs.pydantic.dev/latest/concepts/validators/#field-after-validator) validators are then run from left to right:

```python
from pydantic import AfterValidator, BaseModel, BeforeValidator, WrapValidator

class Model(BaseModel):
    name: Annotated[
        str,
        AfterValidator(runs_3rd),
        AfterValidator(runs_4th),
        BeforeValidator(runs_2nd),
        WrapValidator(runs_1st),
    ]
```

Internally, validators defined using [the decorator](https://docs.pydantic.dev/latest/concepts/validators/#using-the-decorator-pattern) are converted to their annotated form counterpart and added last after the existing metadata for the field. This means that the same ordering logic applies.

## Special types¶

Pydantic provides a few special utilities that can be used to customize validation.

- [`InstanceOf`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.InstanceOf) can be used to validate that a value is an instance of a given class.

```python
from pydantic import BaseModel, InstanceOf, ValidationError

class Fruit:
    def __repr__(self):
        return self.__class__.__name__

class Banana(Fruit): ...

class Apple(Fruit): ...

class Basket(BaseModel):
    fruits: list[InstanceOf[Fruit]]

print(Basket(fruits=[Banana(), Apple()]))
#> fruits=[Banana, Apple]
try:
    Basket(fruits=[Banana(), 'Apple'])
except ValidationError as e:
    print(e)
    """
    1 validation error for Basket
    fruits.1
      Input should be an instance of Fruit [type=is_instance_of, input_value='Apple', input_type=str]
    """
```
- [`SkipValidation`](https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.SkipValidation) can be used to skip validation on a field.

```python
from pydantic import BaseModel, SkipValidation

class Model(BaseModel):
    names: list[SkipValidation[str]]

m = Model(names=['foo', 'bar'])
print(m)
#> names=['foo', 'bar']

m = Model(names=['foo', 123])  
print(m)
#> names=['foo', 123]
```
- [`PydanticUseDefault`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.PydanticUseDefault) can be used to notify Pydantic that the default value should be used.

```python
from typing import Annotated, Any

from pydantic_core import PydanticUseDefault

from pydantic import BaseModel, BeforeValidator

def default_if_none(value: Any) -> Any:
    if value is None:
        raise PydanticUseDefault()
    return value

class Model(BaseModel):
    name: Annotated[str, BeforeValidator(default_if_none)] = 'default_name'

print(Model(name=None))
#> name='default_name'
```

## JSON Schema and field validators¶

When using [*before*](https://docs.pydantic.dev/latest/concepts/validators/#field-before-validator), [*plain*](https://docs.pydantic.dev/latest/concepts/validators/#field-plain-validator) or [*wrap*](https://docs.pydantic.dev/latest/concepts/validators/#field-wrap-validator) field validators, the accepted input type may be different from the field annotation.

Consider the following example:

```python
from typing import Any

from pydantic import BaseModel, field_validator

class Model(BaseModel):
    value: str

    @field_validator('value', mode='before')
    @classmethod
    def cast_ints(cls, value: Any) -> Any:
        if isinstance(value, int):
            return str(value)
        else:
            return value

print(Model(value='a'))
#> value='a'
print(Model(value=1))
#> value='1'
```

While the type hint for `value` is `str`, the `cast_ints` validator also allows integers. To specify the correct input type, the `json_schema_input_type` argument can be provided:

```python
from typing import Any, Union

from pydantic import BaseModel, field_validator

class Model(BaseModel):
    value: str

    @field_validator(
        'value', mode='before', json_schema_input_type=Union[int, str]
    )
    @classmethod
    def cast_ints(cls, value: Any) -> Any:
        if isinstance(value, int):
            return str(value)
        else:
            return value

print(Model.model_json_schema()['properties']['value'])
#> {'anyOf': [{'type': 'integer'}, {'type': 'string'}], 'title': 'Value'}
```

As a convenience, Pydantic will use the field type if the argument is not provided (unless you are using a [*plain*](https://docs.pydantic.dev/latest/concepts/validators/#field-plain-validator) validator, in which case `json_schema_input_type` defaults to [`Any`](https://docs.python.org/3/library/typing.html#typing.Any) as the field type is completely discarded).
---
title: "Dataclasses - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/dataclasses/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
API Documentation

[`pydantic.dataclasses.dataclass`](https://docs.pydantic.dev/latest/api/dataclasses/#pydantic.dataclasses.dataclass)  

If you don't want to use Pydantic's [`BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel) you can instead get the same data validation on standard [dataclasses](https://docs.python.org/3/library/dataclasses.html#module-dataclasses).

```
from datetime import datetime
from typing import Optional

from pydantic.dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None

user = User(id='42', signup_ts='2032-06-21T12:00')
print(user)
"""
User(id=42, name='John Doe', signup_ts=datetime.datetime(2032, 6, 21, 12, 0))
"""
```

```
from datetime import datetime

from pydantic.dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: datetime | None = None

user = User(id='42', signup_ts='2032-06-21T12:00')
print(user)
"""
User(id=42, name='John Doe', signup_ts=datetime.datetime(2032, 6, 21, 12, 0))
"""
```

Note

Keep in mind that Pydantic dataclasses are **not** a replacement for [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/). They provide a similar functionality to stdlib dataclasses with the addition of Pydantic validation.

There are cases where subclassing using Pydantic models is the better choice.

For more information and discussion see [pydantic/pydantic#710](https://github.com/pydantic/pydantic/issues/710).

Similarities between Pydantic dataclasses and models include support for:

- [Configuration](https://docs.pydantic.dev/latest/concepts/dataclasses/#dataclass-config) support
- [Nested](https://docs.pydantic.dev/latest/concepts/models/#nested-models) classes
- [Generics](https://docs.pydantic.dev/latest/concepts/models/#generic-models)

Some differences between Pydantic dataclasses and models include:

- [validators](https://docs.pydantic.dev/latest/concepts/dataclasses/#validators-and-initialization-hooks)
- The behavior with the [`extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) configuration value

Similarly to Pydantic models, arguments used to instantiate the dataclass are [copied](https://docs.pydantic.dev/latest/concepts/models/#attribute-copies).

To make use of the [various methods](https://docs.pydantic.dev/latest/concepts/models/#model-methods-and-properties) to validate, dump and generate a JSON Schema, you can wrap the dataclass with a [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) and make use of its methods.

You can use both the Pydantic's [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) and the stdlib's [`field()`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field) functions:

```
import dataclasses
from typing import Optional

from pydantic import Field, TypeAdapter
from pydantic.dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: list[int] = dataclasses.field(default_factory=lambda: [0])
    age: Optional[int] = dataclasses.field(
        default=None,
        metadata={'title': 'The age of the user', 'description': 'do not lie!'},
    )
    height: Optional[int] = Field(None, title='The height in cm', ge=50, le=300)

user = User(id='42')
print(TypeAdapter(User).json_schema())
"""
{
    'properties': {
        'id': {'title': 'Id', 'type': 'integer'},
        'name': {'default': 'John Doe', 'title': 'Name', 'type': 'string'},
        'friends': {
            'items': {'type': 'integer'},
            'title': 'Friends',
            'type': 'array',
        },
        'age': {
            'anyOf': [{'type': 'integer'}, {'type': 'null'}],
            'default': None,
            'description': 'do not lie!',
            'title': 'The age of the user',
        },
        'height': {
            'anyOf': [
                {'maximum': 300, 'minimum': 50, 'type': 'integer'},
                {'type': 'null'},
            ],
            'default': None,
            'title': 'The height in cm',
        },
    },
    'required': ['id'],
    'title': 'User',
    'type': 'object',
}
"""
```

```
import dataclasses

from pydantic import Field, TypeAdapter
from pydantic.dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: list[int] = dataclasses.field(default_factory=lambda: [0])
    age: int | None = dataclasses.field(
        default=None,
        metadata={'title': 'The age of the user', 'description': 'do not lie!'},
    )
    height: int | None = Field(None, title='The height in cm', ge=50, le=300)

user = User(id='42')
print(TypeAdapter(User).json_schema())
"""
{
    'properties': {
        'id': {'title': 'Id', 'type': 'integer'},
        'name': {'default': 'John Doe', 'title': 'Name', 'type': 'string'},
        'friends': {
            'items': {'type': 'integer'},
            'title': 'Friends',
            'type': 'array',
        },
        'age': {
            'anyOf': [{'type': 'integer'}, {'type': 'null'}],
            'default': None,
            'description': 'do not lie!',
            'title': 'The age of the user',
        },
        'height': {
            'anyOf': [
                {'maximum': 300, 'minimum': 50, 'type': 'integer'},
                {'type': 'null'},
            ],
            'default': None,
            'title': 'The height in cm',
        },
    },
    'required': ['id'],
    'title': 'User',
    'type': 'object',
}
"""
```

The Pydantic `@dataclass` decorator accepts the same arguments as the standard decorator, with the addition of a `config` parameter.

## Dataclass config¶

If you want to modify the configuration like you would with a [`BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel), you have two options:

- Use the `config` argument of the decorator.
- Define the configuration with the `__pydantic_config__` attribute.

```python
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

# Option 1 -- using the decorator argument:
@dataclass(config=ConfigDict(validate_assignment=True))  
class MyDataclass1:
    a: int

# Option 2 -- using an attribute:
@dataclass
class MyDataclass2:
    a: int

    __pydantic_config__ = ConfigDict(validate_assignment=True)
```

Note

While Pydantic dataclasses support the [`extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) configuration value, some default behavior of stdlib dataclasses may prevail. For example, any extra fields present on a Pydantic dataclass with [`extra`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) set to `'allow'` are omitted in the dataclass' string representation. There is also no way to provide validation [using the `__pydantic_extra__` attribute](https://docs.pydantic.dev/latest/concepts/models/#extra-data).

## Rebuilding dataclass schema¶

The [`rebuild_dataclass()`](https://docs.pydantic.dev/latest/api/dataclasses/#pydantic.dataclasses.rebuild_dataclass) can be used to rebuild the core schema of the dataclass. See the [rebuilding model schema](https://docs.pydantic.dev/latest/concepts/models/#rebuilding-model-schema) section for more details.

## Stdlib dataclasses and Pydantic dataclasses¶
### Inherit from stdlib dataclasses¶

Stdlib dataclasses (nested or not) can also be inherited and Pydantic will automatically validate all the inherited fields.

```python
import dataclasses

import pydantic

@dataclasses.dataclass
class Z:
    z: int

@dataclasses.dataclass
class Y(Z):
    y: int = 0

@pydantic.dataclasses.dataclass
class X(Y):
    x: int = 0

foo = X(x=b'1', y='2', z='3')
print(foo)
#> X(z=3, y=2, x=1)

try:
    X(z='pika')
except pydantic.ValidationError as e:
    print(e)
    """
    1 validation error for X
    z
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='pika', input_type=str]
    """
```

### Usage of stdlib dataclasses with `BaseModel`[¶](https://docs.pydantic.dev/latest/concepts/dataclasses/#usage-of-stdlib-dataclasses-with-basemodel "Permanent link")

When a standard library dataclass is used within a Pydantic model, a Pydantic dataclass or a [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter), validation will be applied (and the [configuration](https://docs.pydantic.dev/latest/concepts/dataclasses/#dataclass-config) stays the same). This means that using a stdlib or a Pydantic dataclass as a field annotation is functionally equivalent.

```
import dataclasses
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError

@dataclasses.dataclass(frozen=True)
class User:
    name: str

class Foo(BaseModel):
    # Required so that pydantic revalidates the model attributes:
    model_config = ConfigDict(revalidate_instances='always')

    user: Optional[User] = None

# nothing is validated as expected:
user = User(name=['not', 'a', 'string'])
print(user)
#> User(name=['not', 'a', 'string'])

try:
    Foo(user=user)
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    user.name
      Input should be a valid string [type=string_type, input_value=['not', 'a', 'string'], input_type=list]
    """

foo = Foo(user=User(name='pika'))
try:
    foo.user.name = 'bulbi'
except dataclasses.FrozenInstanceError as e:
    print(e)
    #> cannot assign to field 'name'
```

```
import dataclasses

from pydantic import BaseModel, ConfigDict, ValidationError

@dataclasses.dataclass(frozen=True)
class User:
    name: str

class Foo(BaseModel):
    # Required so that pydantic revalidates the model attributes:
    model_config = ConfigDict(revalidate_instances='always')

    user: User | None = None

# nothing is validated as expected:
user = User(name=['not', 'a', 'string'])
print(user)
#> User(name=['not', 'a', 'string'])

try:
    Foo(user=user)
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    user.name
      Input should be a valid string [type=string_type, input_value=['not', 'a', 'string'], input_type=list]
    """

foo = Foo(user=User(name='pika'))
try:
    foo.user.name = 'bulbi'
except dataclasses.FrozenInstanceError as e:
    print(e)
    #> cannot assign to field 'name'
```

### Using custom types¶

As said above, validation is applied on standard library dataclasses. If you make use of custom types, you will get an error when trying to refer to the dataclass. To circumvent the issue, you can set the [`arbitrary_types_allowed`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.arbitrary_types_allowed) configuration value on the dataclass:

```python
import dataclasses

from pydantic import BaseModel, ConfigDict
from pydantic.errors import PydanticSchemaGenerationError

class ArbitraryType:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'ArbitraryType(value={self.value!r})'

@dataclasses.dataclass
class DC:
    a: ArbitraryType
    b: str

# valid as it is a stdlib dataclass without validation:
my_dc = DC(a=ArbitraryType(value=3), b='qwe')

try:

    class Model(BaseModel):
        dc: DC
        other: str

    # invalid as dc is now validated with pydantic, and ArbitraryType is not a known type
    Model(dc=my_dc, other='other')

except PydanticSchemaGenerationError as e:
    print(e.message)
    """
    Unable to generate pydantic-core schema for <class '__main__.ArbitraryType'>. Set \`arbitrary_types_allowed=True\` in the model_config to ignore this error or implement \`__get_pydantic_core_schema__\` on your type to fully support it.

    If you got this error by calling handler(<some type>) within \`__get_pydantic_core_schema__\` then you likely need to call \`handler.generate_schema(<some type>)\` since we do not call \`__get_pydantic_core_schema__\` on \`<some type>\` otherwise to avoid infinite recursion.
    """

# valid as we set arbitrary_types_allowed=True, and that config pushes down to the nested vanilla dataclass
class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dc: DC
    other: str

m = Model(dc=my_dc, other='other')
print(repr(m))
#> Model(dc=DC(a=ArbitraryType(value=3), b='qwe'), other='other')
```

### Checking if a dataclass is a Pydantic dataclass¶

Pydantic dataclasses are still considered dataclasses, so using [`dataclasses.is_dataclass`](https://docs.python.org/3/library/dataclasses.html#dataclasses.is_dataclass) will return `True`. To check if a type is specifically a pydantic dataclass you can use the [`is_pydantic_dataclass`](https://docs.pydantic.dev/latest/api/dataclasses/#pydantic.dataclasses.is_pydantic_dataclass) function.

```python
import dataclasses

import pydantic

@dataclasses.dataclass
class StdLibDataclass:
    id: int

PydanticDataclass = pydantic.dataclasses.dataclass(StdLibDataclass)

print(dataclasses.is_dataclass(StdLibDataclass))
#> True
print(pydantic.dataclasses.is_pydantic_dataclass(StdLibDataclass))
#> False

print(dataclasses.is_dataclass(PydanticDataclass))
#> True
print(pydantic.dataclasses.is_pydantic_dataclass(PydanticDataclass))
#> True
```

## Validators and initialization hooks¶

Validators also work with Pydantic dataclasses:

```python
from pydantic import field_validator
from pydantic.dataclasses import dataclass

@dataclass
class DemoDataclass:
    product_id: str  # should be a five-digit string, may have leading zeros

    @field_validator('product_id', mode='before')
    @classmethod
    def convert_int_serial(cls, v):
        if isinstance(v, int):
            v = str(v).zfill(5)
        return v

print(DemoDataclass(product_id='01234'))
#> DemoDataclass(product_id='01234')
print(DemoDataclass(product_id=2468))
#> DemoDataclass(product_id='02468')
```

The dataclass [`__post_init__()`](https://docs.python.org/3/library/dataclasses.html#dataclasses.__post_init__) method is also supported, and will be called between the calls to *before* and *after* model validators.

Example

```python
from pydantic_core import ArgsKwargs
from typing_extensions import Self

from pydantic import model_validator
from pydantic.dataclasses import dataclass

@dataclass
class Birth:
    year: int
    month: int
    day: int

@dataclass
class User:
    birth: Birth

    @model_validator(mode='before')
    @classmethod
    def before(cls, values: ArgsKwargs) -> ArgsKwargs:
        print(f'First: {values}')  
        """
        First: ArgsKwargs((), {'birth': {'year': 1995, 'month': 3, 'day': 2}})
        """
        return values

    @model_validator(mode='after')
    def after(self) -> Self:
        print(f'Third: {self}')
        #> Third: User(birth=Birth(year=1995, month=3, day=2))
        return self

    def __post_init__(self):
        print(f'Second: {self.birth}')
        #> Second: Birth(year=1995, month=3, day=2)

user = User(**{'birth': {'year': 1995, 'month': 3, 'day': 2}})
```
---
title: "Forward Annotations - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/forward_annotations/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
Forward annotations (wrapped in quotes) or using the `from __future__ import annotations` [future statement](https://docs.python.org/3/reference/simple_stmts.html#future) (as introduced in [PEP563](https://www.python.org/dev/peps/pep-0563/)) are supported:

```python
from __future__ import annotations

from pydantic import BaseModel

MyInt = int

class Model(BaseModel):
    a: MyInt
    # Without the future import, equivalent to:
    # a: 'MyInt'

print(Model(a='1'))
#> a=1
```

As shown in the following sections, forward annotations are useful when you want to reference a type that is not yet defined in your code.

The internal logic to resolve forward annotations is described in detail in [this section](https://docs.pydantic.dev/latest/internals/resolving_annotations/).

## Self-referencing (or "Recursive") Models¶

Models with self-referencing fields are also supported. These annotations will be resolved during model creation.

Within the model, you can either add the `from __future__ import annotations` import or wrap the annotation in a string:

```python
from typing import Optional

from pydantic import BaseModel

class Foo(BaseModel):
    a: int = 123
    sibling: 'Optional[Foo]' = None

print(Foo())
#> a=123 sibling=None
print(Foo(sibling={'a': '321'}))
#> a=123 sibling=Foo(a=321, sibling=None)
```

### Cyclic references¶

When working with self-referencing recursive models, it is possible that you might encounter cyclic references in validation inputs. For example, this can happen when validating ORM instances with back-references from attributes.

Rather than raising a [`RecursionError`](https://docs.python.org/3/library/exceptions.html#RecursionError) while attempting to validate data with cyclic references, Pydantic is able to detect the cyclic reference and raise an appropriate [`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError):

```
from typing import Optional

from pydantic import BaseModel, ValidationError

class ModelA(BaseModel):
    b: 'Optional[ModelB]' = None

class ModelB(BaseModel):
    a: Optional[ModelA] = None

cyclic_data = {}
cyclic_data['a'] = {'b': cyclic_data}
print(cyclic_data)
#> {'a': {'b': {...}}}

try:
    ModelB.model_validate(cyclic_data)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for ModelB
    a.b
      Recursion error - cyclic reference detected [type=recursion_loop, input_value={'a': {'b': {...}}}, input_type=dict]
    """
```

```
from typing import Optional

from pydantic import BaseModel, ValidationError

class ModelA(BaseModel):
    b: 'Optional[ModelB]' = None

class ModelB(BaseModel):
    a: ModelA | None = None

cyclic_data = {}
cyclic_data['a'] = {'b': cyclic_data}
print(cyclic_data)
#> {'a': {'b': {...}}}

try:
    ModelB.model_validate(cyclic_data)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for ModelB
    a.b
      Recursion error - cyclic reference detected [type=recursion_loop, input_value={'a': {'b': {...}}}, input_type=dict]
    """
```

Because this error is raised without actually exceeding the maximum recursion depth, you can catch and handle the raised [`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) without needing to worry about the limited remaining recursion depth:

```
from contextlib import contextmanager
from dataclasses import field
from typing import Iterator

from pydantic import BaseModel, ValidationError, field_validator

def is_recursion_validation_error(exc: ValidationError) -> bool:
    errors = exc.errors()
    return len(errors) == 1 and errors[0]['type'] == 'recursion_loop'

@contextmanager
def suppress_recursion_validation_error() -> Iterator[None]:
    try:
        yield
    except ValidationError as exc:
        if not is_recursion_validation_error(exc):
            raise exc

class Node(BaseModel):
    id: int
    children: list['Node'] = field(default_factory=list)

    @field_validator('children', mode='wrap')
    @classmethod
    def drop_cyclic_references(cls, children, h):
        try:
            return h(children)
        except ValidationError as exc:
            if not (
                is_recursion_validation_error(exc)
                and isinstance(children, list)
            ):
                raise exc

            value_without_cyclic_refs = []
            for child in children:
                with suppress_recursion_validation_error():
                    value_without_cyclic_refs.extend(h([child]))
            return h(value_without_cyclic_refs)

# Create data with cyclic references representing the graph 1 -> 2 -> 3 -> 1
node_data = {'id': 1, 'children': [{'id': 2, 'children': [{'id': 3}]}]}
node_data['children'][0]['children'][0]['children'] = [node_data]

print(Node.model_validate(node_data))
#> id=1 children=[Node(id=2, children=[Node(id=3, children=[])])]
```

```
from contextlib import contextmanager
from dataclasses import field
from collections.abc import Iterator

from pydantic import BaseModel, ValidationError, field_validator

def is_recursion_validation_error(exc: ValidationError) -> bool:
    errors = exc.errors()
    return len(errors) == 1 and errors[0]['type'] == 'recursion_loop'

@contextmanager
def suppress_recursion_validation_error() -> Iterator[None]:
    try:
        yield
    except ValidationError as exc:
        if not is_recursion_validation_error(exc):
            raise exc

class Node(BaseModel):
    id: int
    children: list['Node'] = field(default_factory=list)

    @field_validator('children', mode='wrap')
    @classmethod
    def drop_cyclic_references(cls, children, h):
        try:
            return h(children)
        except ValidationError as exc:
            if not (
                is_recursion_validation_error(exc)
                and isinstance(children, list)
            ):
                raise exc

            value_without_cyclic_refs = []
            for child in children:
                with suppress_recursion_validation_error():
                    value_without_cyclic_refs.extend(h([child]))
            return h(value_without_cyclic_refs)

# Create data with cyclic references representing the graph 1 -> 2 -> 3 -> 1
node_data = {'id': 1, 'children': [{'id': 2, 'children': [{'id': 3}]}]}
node_data['children'][0]['children'][0]['children'] = [node_data]

print(Node.model_validate(node_data))
#> id=1 children=[Node(id=2, children=[Node(id=3, children=[])])]
```

Similarly, if Pydantic encounters a recursive reference during *serialization*, rather than waiting for the maximum recursion depth to be exceeded, a [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError) is raised immediately:

```python
from pydantic import TypeAdapter

# Create data with cyclic references representing the graph 1 -> 2 -> 3 -> 1
node_data = {'id': 1, 'children': [{'id': 2, 'children': [{'id': 3}]}]}
node_data['children'][0]['children'][0]['children'] = [node_data]

try:
    # Try serializing the circular reference as JSON
    TypeAdapter(dict).dump_json(node_data)
except ValueError as exc:
    print(exc)
    """
    Error serializing to JSON: ValueError: Circular reference detected (id repeated)
    """
```

This can also be handled if desired:

```python
from dataclasses import field
from typing import Any

from pydantic import (
    SerializerFunctionWrapHandler,
    TypeAdapter,
    field_serializer,
)
from pydantic.dataclasses import dataclass

@dataclass
class NodeReference:
    id: int

@dataclass
class Node(NodeReference):
    children: list['Node'] = field(default_factory=list)

    @field_serializer('children', mode='wrap')
    def serialize(
        self, children: list['Node'], handler: SerializerFunctionWrapHandler
    ) -> Any:
        """
        Serialize a list of nodes, handling circular references by excluding the children.
        """
        try:
            return handler(children)
        except ValueError as exc:
            if not str(exc).startswith('Circular reference'):
                raise exc

            result = []
            for node in children:
                try:
                    serialized = handler([node])
                except ValueError as exc:
                    if not str(exc).startswith('Circular reference'):
                        raise exc
                    result.append({'id': node.id})
                else:
                    result.append(serialized)
            return result

# Create a cyclic graph:
nodes = [Node(id=1), Node(id=2), Node(id=3)]
nodes[0].children.append(nodes[1])
nodes[1].children.append(nodes[2])
nodes[2].children.append(nodes[0])

print(nodes[0])
#> Node(id=1, children=[Node(id=2, children=[Node(id=3, children=[...])])])

# Serialize the cyclic graph:
print(TypeAdapter(Node).dump_python(nodes[0]))
"""
{
    'id': 1,
    'children': [{'id': 2, 'children': [{'id': 3, 'children': [{'id': 1}]}]}],
}
"""
```
---
title: "Strict Mode - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/strict_mode/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
API Documentation

[`pydantic.types.Strict`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.Strict)  

By default, Pydantic will attempt to coerce values to the desired type when possible. For example, you can pass the string `"123"` as the input to an `int` field, and it will be converted to `123`. This coercion behavior is useful in many scenarios — think: UUIDs, URL parameters, HTTP headers, environment variables, user input, etc.

However, there are also situations where this is not desirable, and you want Pydantic to error instead of coercing data.

To better support this use case, Pydantic provides a "strict mode" that can be enabled on a per-model, per-field, or even per-validation-call basis. When strict mode is enabled, Pydantic will be much less lenient when coercing data, and will instead error if the data is not of the correct type.

Here is a brief example showing the difference between validation behavior in strict and the default/"lax" mode:

```python
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    x: int

print(MyModel.model_validate({'x': '123'}))  # lax mode
#> x=123

try:
    MyModel.model_validate({'x': '123'}, strict=True)  # strict mode
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyModel
    x
      Input should be a valid integer [type=int_type, input_value='123', input_type=str]
    """
```

There are various ways to get strict-mode validation while using Pydantic, which will be discussed in more detail below:

- [Passing `strict=True` to the validation methods](https://docs.pydantic.dev/latest/concepts/strict_mode/#strict-mode-in-method-calls), such as `BaseModel.model_validate`, `TypeAdapter.validate_python`, and similar for JSON
- [Using `Field(strict=True)`](https://docs.pydantic.dev/latest/concepts/strict_mode/#strict-mode-with-field) with fields of a `BaseModel`, `dataclass`, or `TypedDict`
- [Using `pydantic.types.Strict` as a type annotation](https://docs.pydantic.dev/latest/concepts/strict_mode/#strict-mode-with-annotated-strict) on a field
- Pydantic provides some type aliases that are already annotated with `Strict`, such as `pydantic.types.StrictInt`
- [Using `ConfigDict(strict=True)`](https://docs.pydantic.dev/latest/concepts/strict_mode/#strict-mode-with-configdict)

## Type coercions in strict mode¶

For most types, when validating data from python in strict mode, only the instances of the exact types are accepted. For example, when validating an `int` field, only instances of `int` are accepted; passing instances of `float` or `str` will result in raising a `ValidationError`.

Note that we are looser when validating data from JSON in strict mode. For example, when validating a `UUID` field, instances of `str` will be accepted when validating from JSON, but not from python:

```python
import json
from uuid import UUID

from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    guid: UUID

data = {'guid': '12345678-1234-1234-1234-123456789012'}

print(MyModel.model_validate(data))  # OK: lax
#> guid=UUID('12345678-1234-1234-1234-123456789012')

print(
    MyModel.model_validate_json(json.dumps(data), strict=True)
)  # OK: strict, but from json
#> guid=UUID('12345678-1234-1234-1234-123456789012')

try:
    MyModel.model_validate(data, strict=True)  # Not OK: strict, from python
except ValidationError as exc:
    print(exc.errors(include_url=False))
    """
    [
        {
            'type': 'is_instance_of',
            'loc': ('guid',),
            'msg': 'Input should be an instance of UUID',
            'input': '12345678-1234-1234-1234-123456789012',
            'ctx': {'class': 'UUID'},
        }
    ]
    """
```

For more details about what types are allowed as inputs in strict mode, you can review the [Conversion Table](https://docs.pydantic.dev/latest/concepts/conversion_table/).

## Strict mode in method calls¶

All the examples included so far get strict-mode validation through the use of `strict=True` as a keyword argument to the validation methods. While we have shown this for `BaseModel.model_validate`, this also works with arbitrary types through the use of `TypeAdapter`:

```python
from pydantic import TypeAdapter, ValidationError

print(TypeAdapter(bool).validate_python('yes'))  # OK: lax
#> True

try:
    TypeAdapter(bool).validate_python('yes', strict=True)  # Not OK: strict
except ValidationError as exc:
    print(exc)
    """
    1 validation error for bool
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

Note this also works even when using more "complex" types in `TypeAdapter`:

```python
from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError

@dataclass
class MyDataclass:
    x: int

try:
    TypeAdapter(MyDataclass).validate_python({'x': '123'}, strict=True)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyDataclass
      Input should be an instance of MyDataclass [type=dataclass_exact_type, input_value={'x': '123'}, input_type=dict]
    """
```

This also works with the `TypeAdapter.validate_json` and `BaseModel.model_validate_json` methods:

```python
import json
from uuid import UUID

from pydantic import BaseModel, TypeAdapter, ValidationError

try:
    TypeAdapter(list[int]).validate_json('["1", 2, "3"]', strict=True)
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for list[int]
    0
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    2
      Input should be a valid integer [type=int_type, input_value='3', input_type=str]
    """

class Model(BaseModel):
    x: int
    y: UUID

data = {'x': '1', 'y': '12345678-1234-1234-1234-123456789012'}
try:
    Model.model_validate(data, strict=True)
except ValidationError as exc:
    # Neither x nor y are valid in strict mode from python:
    print(exc)
    """
    2 validation errors for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    y
      Input should be an instance of UUID [type=is_instance_of, input_value='12345678-1234-1234-1234-123456789012', input_type=str]
    """

json_data = json.dumps(data)
try:
    Model.model_validate_json(json_data, strict=True)
except ValidationError as exc:
    # From JSON, x is still not valid in strict mode, but y is:
    print(exc)
    """
    1 validation error for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

## Strict mode with `Field`[¶](https://docs.pydantic.dev/latest/concepts/strict_mode/#strict-mode-with-field "Permanent link")

For individual fields on a model, you can [set `strict=True` on the field](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field). This will cause strict-mode validation to be used for that field, even when the validation methods are called without `strict=True`.

Only the fields for which `strict=True` is set will be affected:

```python
from pydantic import BaseModel, Field, ValidationError

class User(BaseModel):
    name: str
    age: int
    n_pets: int

user = User(name='John', age='42', n_pets='1')
print(user)
#> name='John' age=42 n_pets=1

class AnotherUser(BaseModel):
    name: str
    age: int = Field(strict=True)
    n_pets: int

try:
    anotheruser = AnotherUser(name='John', age='42', n_pets='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for AnotherUser
    age
      Input should be a valid integer [type=int_type, input_value='42', input_type=str]
    """
```

Note that making fields strict will also affect the validation performed when instantiating the model class:

```python
from pydantic import BaseModel, Field, ValidationError

class Model(BaseModel):
    x: int = Field(strict=True)
    y: int = Field(strict=False)

try:
    Model(x='1', y='2')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

### Using `Field` as an annotation[¶](https://docs.pydantic.dev/latest/concepts/strict_mode/#using-field-as-an-annotation "Permanent link")

Note that `Field(strict=True)` (or with any other keyword arguments) can be used as an annotation if necessary, e.g., when working with `TypedDict`:

```
from typing import Annotated

from typing_extensions import TypedDict

from pydantic import Field, TypeAdapter, ValidationError

class MyDict(TypedDict):
    x: Annotated[int, Field(strict=True)]

try:
    TypeAdapter(MyDict).validate_python({'x': '1'})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyDict
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

```
from typing import Annotated

from typing import TypedDict

from pydantic import Field, TypeAdapter, ValidationError

class MyDict(TypedDict):
    x: Annotated[int, Field(strict=True)]

try:
    TypeAdapter(MyDict).validate_python({'x': '1'})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyDict
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

## Strict mode with `Annotated[..., Strict()]`[¶](https://docs.pydantic.dev/latest/concepts/strict_mode/#strict-mode-with-annotated-strict "Permanent link")

API Documentation

[`pydantic.types.Strict`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.Strict)  

Pydantic also provides the [`Strict`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.Strict) class, which is intended for use as metadata with [`typing.Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) class; this annotation indicates that the annotated field should be validated in strict mode:

```python
from typing import Annotated

from pydantic import BaseModel, Strict, ValidationError

class User(BaseModel):
    name: str
    age: int
    is_active: Annotated[bool, Strict()]

User(name='David', age=33, is_active=True)
try:
    User(name='David', age=33, is_active='True')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for User
    is_active
      Input should be a valid boolean [type=bool_type, input_value='True', input_type=str]
    """
```

This is, in fact, the method used to implement some of the strict-out-of-the-box types provided by Pydantic, such as [`StrictInt`](https://docs.pydantic.dev/latest/api/types/#pydantic.types.StrictInt).

## Strict mode with `ConfigDict`[¶](https://docs.pydantic.dev/latest/concepts/strict_mode/#strict-mode-with-configdict "Permanent link")

### `BaseModel`[¶](https://docs.pydantic.dev/latest/concepts/strict_mode/#basemodel "Permanent link")

If you want to enable strict mode for all fields on a complex input type, you can use [`ConfigDict(strict=True)`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict) in the `model_config`:

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class User(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int
    is_active: bool

try:
    User(name='David', age='33', is_active='yes')
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for User
    age
      Input should be a valid integer [type=int_type, input_value='33', input_type=str]
    is_active
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

Note

When using `strict=True` through a model's `model_config`, you can still override the strictness of individual fields by setting `strict=False` on individual fields:

```python
from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int = Field(strict=False)
```

Note that strict mode is not recursively applied to nested model fields:

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class Inner(BaseModel):
    y: int

class Outer(BaseModel):
    model_config = ConfigDict(strict=True)

    x: int
    inner: Inner

print(Outer(x=1, inner=Inner(y='2')))
#> x=1 inner=Inner(y=2)

try:
    Outer(x='1', inner=Inner(y='2'))
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

(This is also the case for dataclasses and `TypedDict`.)

If this is undesirable, you should make sure that strict mode is enabled for all the types involved. For example, this can be done for model classes by using a shared base class with `model_config = ConfigDict(strict=True)`:

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class MyBaseModel(BaseModel):
    model_config = ConfigDict(strict=True)

class Inner(MyBaseModel):
    y: int

class Outer(MyBaseModel):
    x: int
    inner: Inner

try:
    Outer.model_validate({'x': 1, 'inner': {'y': '2'}})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    inner.y
      Input should be a valid integer [type=int_type, input_value='2', input_type=str]
    """
```

### Dataclasses and `TypedDict`[¶](https://docs.pydantic.dev/latest/concepts/strict_mode/#dataclasses-and-typeddict "Permanent link")

Pydantic dataclasses behave similarly to the examples shown above with `BaseModel`, just that instead of `model_config` you should use the `config` keyword argument to the `@pydantic.dataclasses.dataclass` decorator.

When possible, you can achieve nested strict mode for vanilla dataclasses or `TypedDict` subclasses by annotating fields with the [`pydantic.types.Strict` annotation](https://docs.pydantic.dev/latest/concepts/strict_mode/#strict-mode-with-annotated-strict).

However, if this is *not* possible (e.g., when working with third-party types), you can set the config that Pydantic should use for the type by setting the `__pydantic_config__` attribute on the type:

```
from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter, ValidationError

class Inner(TypedDict):
    y: int

Inner.__pydantic_config__ = ConfigDict(strict=True)

class Outer(TypedDict):
    x: int
    inner: Inner

adapter = TypeAdapter(Outer)
print(adapter.validate_python({'x': '1', 'inner': {'y': 2}}))
#> {'x': 1, 'inner': {'y': 2}}

try:
    adapter.validate_python({'x': '1', 'inner': {'y': '2'}})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    inner.y
      Input should be a valid integer [type=int_type, input_value='2', input_type=str]
    """
```

```
from typing import TypedDict

from pydantic import ConfigDict, TypeAdapter, ValidationError

class Inner(TypedDict):
    y: int

Inner.__pydantic_config__ = ConfigDict(strict=True)

class Outer(TypedDict):
    x: int
    inner: Inner

adapter = TypeAdapter(Outer)
print(adapter.validate_python({'x': '1', 'inner': {'y': 2}}))
#> {'x': 1, 'inner': {'y': 2}}

try:
    adapter.validate_python({'x': '1', 'inner': {'y': '2'}})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    inner.y
      Input should be a valid integer [type=int_type, input_value='2', input_type=str]
    """
```

### `TypeAdapter`[¶](https://docs.pydantic.dev/latest/concepts/strict_mode/#typeadapter "Permanent link")

You can also get strict mode through the use of the config keyword argument to the [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/) class:

```python
from pydantic import ConfigDict, TypeAdapter, ValidationError

adapter = TypeAdapter(bool, config=ConfigDict(strict=True))

try:
    adapter.validate_python('yes')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for bool
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

### `@validate_call`[¶](https://docs.pydantic.dev/latest/concepts/strict_mode/#validate_call "Permanent link")

Strict mode is also usable with the [`@validate_call`](https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call) decorator by passing the `config` keyword argument:

```python
from pydantic import ConfigDict, ValidationError, validate_call

@validate_call(config=ConfigDict(strict=True))
def foo(x: int) -> int:
    return x

try:
    foo('1')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for foo
    0
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```
---
title: "Type Adapter - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/type_adapter/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
You may have types that are not `BaseModel`s that you want to validate data against. Or you may want to validate a `list[SomeModel]`, or dump it to JSON.

API Documentation

[`pydantic.type_adapter.TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter)  

For use cases like this, Pydantic provides [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter), which can be used for type validation, serialization, and JSON schema generation without needing to create a [`BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel).

A [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) instance exposes some of the functionality from [`BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel) instance methods for types that do not have such methods (such as dataclasses, primitive types, and more):

```
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError

class User(TypedDict):
    name: str
    id: int

user_list_adapter = TypeAdapter(list[User])
user_list = user_list_adapter.validate_python([{'name': 'Fred', 'id': '3'}])
print(repr(user_list))
#> [{'name': 'Fred', 'id': 3}]

try:
    user_list_adapter.validate_python(
        [{'name': 'Fred', 'id': 'wrong', 'other': 'no'}]
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for list[User]
    0.id
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """

print(repr(user_list_adapter.dump_json(user_list)))
#> b'[{"name":"Fred","id":3}]'
```

```
from typing import TypedDict

from pydantic import TypeAdapter, ValidationError

class User(TypedDict):
    name: str
    id: int

user_list_adapter = TypeAdapter(list[User])
user_list = user_list_adapter.validate_python([{'name': 'Fred', 'id': '3'}])
print(repr(user_list))
#> [{'name': 'Fred', 'id': 3}]

try:
    user_list_adapter.validate_python(
        [{'name': 'Fred', 'id': 'wrong', 'other': 'no'}]
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for list[User]
    0.id
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """

print(repr(user_list_adapter.dump_json(user_list)))
#> b'[{"name":"Fred","id":3}]'
```

`dump_json` returns `bytes`

`TypeAdapter`'s `dump_json` methods returns a `bytes` object, unlike the corresponding method for `BaseModel`, `model_dump_json`, which returns a `str`. The reason for this discrepancy is that in V1, model dumping returned a str type, so this behavior is retained in V2 for backwards compatibility. For the `BaseModel` case, `bytes` are coerced to `str` types, but `bytes` are often the desired end type. Hence, for the new `TypeAdapter` class in V2, the return type is simply `bytes`, which can easily be coerced to a `str` type if desired.

Note

Despite some overlap in use cases with [`RootModel`](https://docs.pydantic.dev/latest/api/root_model/#pydantic.root_model.RootModel), [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) should not be used as a type annotation for specifying fields of a `BaseModel`, etc.

## Parsing data into a specified type¶

[`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) can be used to apply the parsing logic to populate Pydantic models in a more ad-hoc way. This function behaves similarly to [`BaseModel.model_validate`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate), but works with arbitrary Pydantic-compatible types.

This is especially useful when you want to parse results into a type that is not a direct subclass of [`BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel). For example:

```python
from pydantic import BaseModel, TypeAdapter

class Item(BaseModel):
    id: int
    name: str

# \`item_data\` could come from an API call, eg., via something like:
# item_data = requests.get('https://my-api.com/items').json()
item_data = [{'id': 1, 'name': 'My Item'}]

items = TypeAdapter(list[Item]).validate_python(item_data)
print(items)
#> [Item(id=1, name='My Item')]
```

[`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) is capable of parsing data into any of the types Pydantic can handle as fields of a [`BaseModel`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel).

Performance considerations

When creating an instance of [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter), the provided type must be analyzed and converted into a pydantic-core schema. This comes with some non-trivial overhead, so it is recommended to create a `TypeAdapter` for a given type just once and reuse it in loops or other performance-critical code.

## Rebuilding a `TypeAdapter`'s schema[¶](https://docs.pydantic.dev/latest/concepts/type_adapter/#rebuilding-a-typeadapters-schema "Permanent link")

In v2.10+, [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter)'s support deferred schema building and manual rebuilds. This is helpful for the case of:

- Types with forward references
- Types for which core schema builds are expensive

When you initialize a [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) with a type, Pydantic analyzes the type and creates a core schema for it. This core schema contains the information needed to validate and serialize data for that type. See the [architecture documentation](https://docs.pydantic.dev/latest/internals/architecture/) for more information on core schemas.

If you set [`defer_build`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.defer_build) to `True` when initializing a `TypeAdapter`, Pydantic will defer building the core schema until the first time it is needed (for validation or serialization).

In order to manually trigger the building of the core schema, you can call the [`rebuild`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter.rebuild) method on the [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) instance:

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter('MyInt', config=ConfigDict(defer_build=True))

# some time later, the forward reference is defined
MyInt = int

ta.rebuild()
assert ta.validate_python(1) == 1
```
---
title: "Validation Decorator - Pydantic"
source: "https://docs.pydantic.dev/latest/concepts/validation_decorator/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
API Documentation

[`pydantic.validate_call_decorator.validate_call`](https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call)  

The [`validate_call()`](https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call) decorator allows the arguments passed to a function to be parsed and validated using the function's annotations before the function is called.

While under the hood this uses the same approach of model creation and initialisation (see [Validators](https://docs.pydantic.dev/latest/concepts/validators/) for more details), it provides an extremely easy way to apply validation to your code with minimal boilerplate.

Example of usage:

```python
from pydantic import ValidationError, validate_call

@validate_call
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))

a = repeat('hello', 3)
print(a)
#> b'hellohellohello'

b = repeat('x', '4', separator=b' ')
print(b)
#> b'x x x x'

try:
    c = repeat('hello', 'wrong')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for repeat
    1
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """
```

## Parameter types¶

Parameter types are inferred from type annotations on the function, or as [`Any`](https://docs.python.org/3/library/typing.html#typing.Any) if not annotated. All types listed in [types](https://docs.pydantic.dev/latest/concepts/types/) can be validated, including Pydantic models and [custom types](https://docs.pydantic.dev/latest/concepts/types/#custom-types). As with the rest of Pydantic, types are by default coerced by the decorator before they're passed to the actual function:

```python
from datetime import date

from pydantic import validate_call

@validate_call
def greater_than(d1: date, d2: date, *, include_equal=False) -> date:  
    if include_equal:
        return d1 >= d2
    else:
        return d1 > d2

d1 = '2000-01-01'  
d2 = date(2001, 1, 1)
greater_than(d1, d2, include_equal=True)
```

Type coercion like this can be extremely helpful, but also confusing or not desired (see [model data conversion](https://docs.pydantic.dev/latest/concepts/models/#data-conversion)). [Strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) can be enabled by using a [custom configuration](https://docs.pydantic.dev/latest/concepts/validation_decorator/#custom-configuration).

Validating the return value

By default, the return value of the function is **not** validated. To do so, the `validate_return` argument of the decorator can be set to `True`.

## Function signatures¶

The [`validate_call()`](https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call) decorator is designed to work with functions using all possible [parameter configurations](https://docs.python.org/3/glossary.html#term-parameter) and all possible combinations of these:

- Positional or keyword parameters with or without defaults.
- Keyword-only parameters: parameters after `*,`.
- Positional-only parameters: parameters before `, /`.
- Variable positional parameters defined via `*` (often `*args`).
- Variable keyword parameters defined via `**` (often `**kwargs`).

Example

```python
from pydantic import validate_call

@validate_call
def pos_or_kw(a: int, b: int = 2) -> str:
    return f'a={a} b={b}'

print(pos_or_kw(1, b=3))
#> a=1 b=3

@validate_call
def kw_only(*, a: int, b: int = 2) -> str:
    return f'a={a} b={b}'

print(kw_only(a=1))
#> a=1 b=2
print(kw_only(a=1, b=3))
#> a=1 b=3

@validate_call
def pos_only(a: int, b: int = 2, /) -> str:
    return f'a={a} b={b}'

print(pos_only(1))
#> a=1 b=2

@validate_call
def var_args(*args: int) -> str:
    return str(args)

print(var_args(1))
#> (1,)
print(var_args(1, 2, 3))
#> (1, 2, 3)

@validate_call
def var_kwargs(**kwargs: int) -> str:
    return str(kwargs)

print(var_kwargs(a=1))
#> {'a': 1}
print(var_kwargs(a=1, b=2))
#> {'a': 1, 'b': 2}

@validate_call
def armageddon(
    a: int,
    /,
    b: int,
    *c: int,
    d: int,
    e: int = None,
    **f: int,
) -> str:
    return f'a={a} b={b} c={c} d={d} e={e} f={f}'

print(armageddon(1, 2, d=3))
#> a=1 b=2 c=() d=3 e=None f={}
print(armageddon(1, 2, 3, 4, 5, 6, d=8, e=9, f=10, spam=11))
#> a=1 b=2 c=(3, 4, 5, 6) d=8 e=9 f={'f': 10, 'spam': 11}
```

[`Unpack`](https://docs.python.org/3/library/typing.html#typing.Unpack) for keyword parameters

[`Unpack`](https://docs.python.org/3/library/typing.html#typing.Unpack) and typed dictionaries can be used to annotate the variable keyword parameters of a function:

```python
from typing_extensions import TypedDict, Unpack

from pydantic import validate_call

class Point(TypedDict):
    x: int
    y: int

@validate_call
def add_coords(**kwargs: Unpack[Point]) -> int:
    return kwargs['x'] + kwargs['y']

add_coords(x=1, y=2)
```

For reference, see the [related specification section](https://typing.readthedocs.io/en/latest/spec/callables.html#unpack-for-keyword-arguments) and [PEP 692](https://peps.python.org/pep-0692/).

## Using the [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) function to describe function parameters[¶](https://docs.pydantic.dev/latest/concepts/validation_decorator/#using-the-field-function-to-describe-function-parameters "Permanent link")

The [`Field()` function](https://docs.pydantic.dev/latest/concepts/fields/) can also be used with the decorator to provide extra information about the field and validations. If you don't make use of the `default` or `default_factory` parameter, it is recommended to use the [annotated pattern](https://docs.pydantic.dev/latest/concepts/fields/#the-annotated-pattern) (so that type checkers infer the parameter as being required). Otherwise, the [`Field()`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) function can be used as a default value (again, to trick type checkers into thinking a default value is provided for the parameter).

```python
from typing import Annotated

from pydantic import Field, ValidationError, validate_call

@validate_call
def how_many(num: Annotated[int, Field(gt=10)]):
    return num

try:
    how_many(1)
except ValidationError as e:
    print(e)
    """
    1 validation error for how_many
    0
      Input should be greater than 10 [type=greater_than, input_value=1, input_type=int]
    """

@validate_call
def return_value(value: str = Field(default='default value')):
    return value

print(return_value())
#> default value
```

[Aliases](https://docs.pydantic.dev/latest/concepts/fields/#field-aliases) can be used with the decorator as normal:

```python
from typing import Annotated

from pydantic import Field, validate_call

@validate_call
def how_many(num: Annotated[int, Field(gt=10, alias='number')]):
    return num

how_many(number=42)
```

## Accessing the original function¶

The original function which was decorated can still be accessed by using the `raw_function` attribute. This is useful if in some scenarios you trust your input arguments and want to call the function in the most efficient way (see [notes on performance](https://docs.pydantic.dev/latest/concepts/validation_decorator/#performance) below):

```python
from pydantic import validate_call

@validate_call
def repeat(s: str, count: int, *, separator: bytes = b'') -> bytes:
    b = s.encode()
    return separator.join(b for _ in range(count))

a = repeat('hello', 3)
print(a)
#> b'hellohellohello'

b = repeat.raw_function('good bye', 2, separator=b', ')
print(b)
#> b'good bye, good bye'
```

## Async functions¶

[`validate_call()`](https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call) can also be used on async functions:

```python
class Connection:
    async def execute(self, sql, *args):
        return 'testing@example.com'

conn = Connection()
# ignore-above
import asyncio

from pydantic import PositiveInt, ValidationError, validate_call

@validate_call
async def get_user_email(user_id: PositiveInt):
    # \`conn\` is some fictional connection to a database
    email = await conn.execute('select email from users where id=$1', user_id)
    if email is None:
        raise RuntimeError('user not found')
    else:
        return email

async def main():
    email = await get_user_email(123)
    print(email)
    #> testing@example.com
    try:
        await get_user_email(-4)
    except ValidationError as exc:
        print(exc.errors())
        """
        [
            {
                'type': 'greater_than',
                'loc': (0,),
                'msg': 'Input should be greater than 0',
                'input': -4,
                'ctx': {'gt': 0},
                'url': 'https://errors.pydantic.dev/2/v/greater_than',
            }
        ]
        """

asyncio.run(main())
# requires: \`conn.execute()\` that will return \`'testing@example.com'\`
```

## Compatibility with type checkers¶

As the [`validate_call()`](https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call) decorator preserves the decorated function's signature, it should be compatible with type checkers (such as mypy and pyright). However, due to current limitations in the Python type system, the [`raw_function`](https://docs.pydantic.dev/latest/concepts/validation_decorator/#accessing-the-original-function) or other attributes won't be recognized and you will need to suppress the error using (usually with a `# type: ignore` comment).

## Custom configuration¶

Similarly to Pydantic models, the `config` parameter of the decorator can be used to specify a custom configuration:

```python
from pydantic import ConfigDict, ValidationError, validate_call

class Foobar:
    def __init__(self, v: str):
        self.v = v

    def __add__(self, other: 'Foobar') -> str:
        return f'{self} + {other}'

    def __str__(self) -> str:
        return f'Foobar({self.v})'

@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def add_foobars(a: Foobar, b: Foobar):
    return a + b

c = add_foobars(Foobar('a'), Foobar('b'))
print(c)
#> Foobar(a) + Foobar(b)

try:
    add_foobars(1, 2)
except ValidationError as e:
    print(e)
    """
    2 validation errors for add_foobars
    0
      Input should be an instance of Foobar [type=is_instance_of, input_value=1, input_type=int]
    1
      Input should be an instance of Foobar [type=is_instance_of, input_value=2, input_type=int]
    """
```

## Extension — validating arguments before calling a function¶

In some cases, it may be helpful to separate validation of a function's arguments from the function call itself. This might be useful when a particular function is costly/time consuming.

Here's an example of a workaround you can use for that pattern:

```python
from pydantic import validate_call

@validate_call
def validate_foo(a: int, b: int):
    def foo():
        return a + b

    return foo

foo = validate_foo(a=1, b=2)
print(foo())
#> 3
```

## Limitations¶
### Validation exception¶

Currently upon validation failure, a standard Pydantic [`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) is raised (see [model error handling](https://docs.pydantic.dev/latest/concepts/models/#error-handling) for details). This is also true for missing required arguments, where Python normally raises a [`TypeError`](https://docs.python.org/3/library/exceptions.html#TypeError).

### Performance¶

We've made a big effort to make Pydantic as performant as possible. While the inspection of the decorated function is only performed once, there will still be a performance impact when making calls to the function compared to using the original function.

In many situations, this will have little or no noticeable effect. However, be aware that [`validate_call()`](https://docs.pydantic.dev/latest/api/validate_call/#pydantic.validate_call_decorator.validate_call) is not an equivalent or alternative to function definitions in strongly typed languages, and it never will be.
---
title: "Validating File Data - Pydantic"
source: "https://docs.pydantic.dev/latest/examples/files/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
`pydantic` is a great tool for validating data coming from various sources. In this section, we will look at how to validate data from different types of files.

Note

If you're using any of the below file formats to parse configuration / settings, you might want to consider using the [`pydantic-settings`](https://docs.pydantic.dev/latest/api/pydantic_settings/#pydantic_settings) library, which offers builtin support for parsing this type of data.

## JSON data¶

`.json` files are a common way to store key / value data in a human-readable format. Here is an example of a `.json` file:

```json
{
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com"
}
```

To validate this data, we can use a `pydantic` model:

```python
import pathlib

from pydantic import BaseModel, EmailStr, PositiveInt

class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr

json_string = pathlib.Path('person.json').read_text()
person = Person.model_validate_json(json_string)
print(repr(person))
#> Person(name='John Doe', age=30, email='john@example.com')
```

If the data in the file is not valid, `pydantic` will raise a [`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError). Let's say we have the following `.json` file:

```json
{
    "age": -30,
    "email": "not-an-email-address"
}
```

This data is flawed for three reasons: 1. It's missing the `name` field. 2. The `age` field is negative. 3. The `email` field is not a valid email address.

When we try to validate this data, `pydantic` raises a [`ValidationError`](https://docs.pydantic.dev/latest/api/pydantic_core/#pydantic_core.ValidationError) with all of the above issues:

```python
import pathlib

from pydantic import BaseModel, EmailStr, PositiveInt, ValidationError

class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr

json_string = pathlib.Path('person.json').read_text()
try:
    person = Person.model_validate_json(json_string)
except ValidationError as err:
    print(err)
    """
    3 validation errors for Person
    name
    Field required [type=missing, input_value={'age': -30, 'email': 'not-an-email-address'}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2.10/v/missing
    age
    Input should be greater than 0 [type=greater_than, input_value=-30, input_type=int]
        For further information visit https://errors.pydantic.dev/2.10/v/greater_than
    email
    value is not a valid email address: An email address must have an @-sign. [type=value_error, input_value='not-an-email-address', input_type=str]
    """
```

Often, it's the case that you have an abundance of a certain type of data within a `.json` file. For example, you might have a list of people:

```json
[
    {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com"
    },
    {
        "name": "Jane Doe",
        "age": 25,
        "email": "jane@example.com"
    }
]
```

In this case, you can validate the data against a `list[Person]` model:

```python
import pathlib

from pydantic import BaseModel, EmailStr, PositiveInt, TypeAdapter

class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr

person_list_adapter = TypeAdapter(list[Person])  

json_string = pathlib.Path('people.json').read_text()
people = person_list_adapter.validate_json(json_string)
print(people)
#> [Person(name='John Doe', age=30, email='john@example.com'), Person(name='Jane Doe', age=25, email='jane@example.com')]
```

## JSON lines files¶

Similar to validating a list of objects from a `.json` file, you can validate a list of objects from a `.jsonl` file. `.jsonl` files are a sequence of JSON objects separated by newlines.

Consider the following `.jsonl` file:

```json
{"name": "John Doe", "age": 30, "email": "john@example.com"}
{"name": "Jane Doe", "age": 25, "email": "jane@example.com"}
```

We can validate this data with a similar approach to the one we used for `.json` files:

```python
import pathlib

from pydantic import BaseModel, EmailStr, PositiveInt

class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr

json_lines = pathlib.Path('people.jsonl').read_text().splitlines()
people = [Person.model_validate_json(line) for line in json_lines]
print(people)
#> [Person(name='John Doe', age=30, email='john@example.com'), Person(name='Jane Doe', age=25, email='jane@example.com')]
```

## CSV files¶

CSV is one of the most common file formats for storing tabular data. To validate data from a CSV file, you can use the `csv` module from the Python standard library to load the data and validate it against a Pydantic model.

Consider the following CSV file:

```text
name,age,email
John Doe,30,john@example.com
Jane Doe,25,jane@example.com
```

Here's how we validate that data:

```python
import csv

from pydantic import BaseModel, EmailStr, PositiveInt

class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr

with open('people.csv') as f:
    reader = csv.DictReader(f)
    people = [Person.model_validate(row) for row in reader]

print(people)
#> [Person(name='John Doe', age=30, email='john@example.com'), Person(name='Jane Doe', age=25, email='jane@example.com')]
```

## TOML files¶

TOML files are often used for configuration due to their simplicity and readability.

Consider the following TOML file:

```toml
name = "John Doe"
age = 30
email = "john@example.com"
```

Here's how we validate that data:

```python
import tomllib

from pydantic import BaseModel, EmailStr, PositiveInt

class Person(BaseModel):
    name: str
    age: PositiveInt
    email: EmailStr

with open('person.toml', 'rb') as f:
    data = tomllib.load(f)

person = Person.model_validate(data)
print(repr(person))
#> Person(name='John Doe', age=30, email='john@example.com')
```
---
title: "Web and API Requests - Pydantic"
source: "https://docs.pydantic.dev/latest/examples/requests/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
Pydantic models are a great way to validating and serializing data for requests and responses. Pydantic is instrumental in many web frameworks and libraries, such as FastAPI, Django, Flask, and HTTPX.

## `httpx` requests[¶](https://docs.pydantic.dev/latest/examples/requests/#httpx-requests "Permanent link")

[`httpx`](https://www.python-httpx.org/) is a HTTP client for Python 3 with synchronous and asynchronous APIs. In the below example, we query the [JSONPlaceholder API](https://jsonplaceholder.typicode.com/) to get a user's data and validate it with a Pydantic model.

```python
import httpx

from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int
    name: str
    email: EmailStr

url = 'https://jsonplaceholder.typicode.com/users/1'

response = httpx.get(url)
response.raise_for_status()

user = User.model_validate(response.json())
print(repr(user))
#> User(id=1, name='Leanne Graham', email='Sincere@april.biz')
```

The [`TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter) tool from Pydantic often comes in quite handy when working with HTTP requests. Consider a similar example where we are validating a list of users:

```python
from pprint import pprint

import httpx

from pydantic import BaseModel, EmailStr, TypeAdapter

class User(BaseModel):
    id: int
    name: str
    email: EmailStr

url = 'https://jsonplaceholder.typicode.com/users/'  

response = httpx.get(url)
response.raise_for_status()

users_list_adapter = TypeAdapter(list[User])

users = users_list_adapter.validate_python(response.json())
pprint([u.name for u in users])
"""
['Leanne Graham',
 'Ervin Howell',
 'Clementine Bauch',
 'Patricia Lebsack',
 'Chelsey Dietrich',
 'Mrs. Dennis Schulist',
 'Kurtis Weissnat',
 'Nicholas Runolfsdottir V',
 'Glenna Reichert',
 'Clementina DuBuque']
"""
```
---
title: "Queues - Pydantic"
source: "https://docs.pydantic.dev/latest/examples/queues/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
Pydantic is quite helpful for validating data that goes into and comes out of queues. Below, we'll explore how to validate / serialize data with various queue systems.

## Redis queue¶

Redis is a popular in-memory data structure store.

In order to run this example locally, you'll first need to [install Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/) and start your server up locally.

Here's a simple example of how you can use Pydantic to: 1. Serialize data to push to the queue 2. Deserialize and validate data when it's popped from the queue

```python
import redis

from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int
    name: str
    email: EmailStr

r = redis.Redis(host='localhost', port=6379, db=0)
QUEUE_NAME = 'user_queue'

def push_to_queue(user_data: User) -> None:
    serialized_data = user_data.model_dump_json()
    r.rpush(QUEUE_NAME, user_data.model_dump_json())
    print(f'Added to queue: {serialized_data}')

user1 = User(id=1, name='John Doe', email='john@example.com')
user2 = User(id=2, name='Jane Doe', email='jane@example.com')

push_to_queue(user1)
#> Added to queue: {"id":1,"name":"John Doe","email":"john@example.com"}

push_to_queue(user2)
#> Added to queue: {"id":2,"name":"Jane Doe","email":"jane@example.com"}

def pop_from_queue() -> None:
    data = r.lpop(QUEUE_NAME)

    if data:
        user = User.model_validate_json(data)
        print(f'Validated user: {repr(user)}')
    else:
        print('Queue is empty')

pop_from_queue()
#> Validated user: User(id=1, name='John Doe', email='john@example.com')

pop_from_queue()
#> Validated user: User(id=2, name='Jane Doe', email='jane@example.com')

pop_from_queue()
#> Queue is empty
```
---
title: "Databases - Pydantic"
source: "https://docs.pydantic.dev/latest/examples/orms/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
Pydantic serves as a great tool for defining models for ORM (object relational mapping) libraries. ORMs are used to map objects to database tables, and vice versa.

## SQLAlchemy¶

Pydantic can pair with SQLAlchemy, as it can be used to define the schema of the database models.

Code Duplication

If you use Pydantic with SQLAlchemy, you might experience some frustration with code duplication. If you find yourself experiencing this difficulty, you might also consider [`SQLModel`](https://sqlmodel.tiangolo.com/) which integrates Pydantic with SQLAlchemy such that much of the code duplication is eliminated.

If you'd prefer to use pure Pydantic with SQLAlchemy, we recommend using Pydantic models alongside of SQLAlchemy models as shown in the example below. In this case, we take advantage of Pydantic's aliases feature to name a `Column` after a reserved SQLAlchemy field, thus avoiding conflicts.

```python
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from pydantic import BaseModel, ConfigDict, Field

class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata: dict[str, str] = Field(alias='metadata_')

Base = declarative_base()

class MyTableModel(Base):
    __tablename__ = 'my_table'
    id = sa.Column('id', sa.Integer, primary_key=True)
    # 'metadata' is reserved by SQLAlchemy, hence the '_'
    metadata_ = sa.Column('metadata', sa.JSON)

sql_model = MyTableModel(metadata_={'key': 'val'}, id=1)
pydantic_model = MyModel.model_validate(sql_model)

print(pydantic_model.model_dump())
#> {'metadata': {'key': 'val'}}
print(pydantic_model.model_dump(by_alias=True))
#> {'metadata_': {'key': 'val'}}
```

Note

The example above works because aliases have priority over field names for field population. Accessing `SQLModel`'s `metadata` attribute would lead to a `ValidationError`.
---
title: "Custom Validators - Pydantic"
source: "https://docs.pydantic.dev/latest/examples/custom_validators/"
author:
published:
created: 2025-04-01
description: "Data validation using Python type hints"
tags:
  - "clippings"
---
This page provides example snippets for creating more complex, custom validators in Pydantic. Many of these examples are adapted from Pydantic issues and discussions, and are intended to showcase the flexibility and power of Pydantic's validation system.

In this example, we'll construct a custom validator, attached to an [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) type, that ensures a [`datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime) object adheres to a given timezone constraint.

The custom validator supports string specification of the timezone, and will raise an error if the [`datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime) object does not have the correct timezone.

We use `__get_pydantic_core_schema__` in the validator to customize the schema of the annotated type (in this case, [`datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime)), which allows us to add custom validation logic. Notably, we use a `wrap` validator function so that we can perform operations both before and after the default `pydantic` validation of a [`datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime).

```
import datetime as dt
from dataclasses import dataclass
from pprint import pprint
from typing import Annotated, Any, Callable, Optional

import pytz
from pydantic_core import CoreSchema, core_schema

from pydantic import (
    GetCoreSchemaHandler,
    PydanticUserError,
    TypeAdapter,
    ValidationError,
)

@dataclass(frozen=True)
class MyDatetimeValidator:
    tz_constraint: Optional[str] = None

    def tz_constraint_validator(
        self,
        value: dt.datetime,
        handler: Callable,  
    ):
        """Validate tz_constraint and tz_info."""
        # handle naive datetimes
        if self.tz_constraint is None:
            assert (
                value.tzinfo is None
            ), 'tz_constraint is None, but provided value is tz-aware.'
            return handler(value)

        # validate tz_constraint and tz-aware tzinfo
        if self.tz_constraint not in pytz.all_timezones:
            raise PydanticUserError(
                f'Invalid tz_constraint: {self.tz_constraint}',
                code='unevaluable-type-annotation',
            )
        result = handler(value)  
        assert self.tz_constraint == str(
            result.tzinfo
        ), f'Invalid tzinfo: {str(result.tzinfo)}, expected: {self.tz_constraint}'

        return result

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.tz_constraint_validator,
            handler(source_type),
        )

LA = 'America/Los_Angeles'
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
print(
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
)
#> 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    ta.validate_python(
        dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON))
    )
except ValidationError as ve:
    pprint(ve.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Invalid tzinfo: Europe/London, expected: America/Los_Angeles')},
    'input': datetime.datetime(2023, 1, 1, 0, 0, tzinfo=<DstTzInfo 'Europe/London' LMT-1 day, 23:59:00 STD>),
    'loc': (),
    'msg': 'Assertion failed, Invalid tzinfo: Europe/London, expected: America/Los_Angeles',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```

```python
import datetime as dt
from dataclasses import dataclass
from pprint import pprint
from typing import Annotated, Any
from collections.abc import Callable

import pytz
from pydantic_core import CoreSchema, core_schema

from pydantic import (
    GetCoreSchemaHandler,
    PydanticUserError,
    TypeAdapter,
    ValidationError,
)

@dataclass(frozen=True)
class MyDatetimeValidator:
    tz_constraint: str | None = None

    def tz_constraint_validator(
        self,
        value: dt.datetime,
        handler: Callable,  
    ):
        """Validate tz_constraint and tz_info."""
        # handle naive datetimes
        if self.tz_constraint is None:
            assert (
                value.tzinfo is None
            ), 'tz_constraint is None, but provided value is tz-aware.'
            return handler(value)

        # validate tz_constraint and tz-aware tzinfo
        if self.tz_constraint not in pytz.all_timezones:
            raise PydanticUserError(
                f'Invalid tz_constraint: {self.tz_constraint}',
                code='unevaluable-type-annotation',
            )
        result = handler(value)  
        assert self.tz_constraint == str(
            result.tzinfo
        ), f'Invalid tzinfo: {str(result.tzinfo)}, expected: {self.tz_constraint}'

        return result

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.tz_constraint_validator,
            handler(source_type),
        )

LA = 'America/Los_Angeles'
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(LA)])
print(
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
)
#> 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    ta.validate_python(
        dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON))
    )
except ValidationError as ve:
    pprint(ve.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Invalid tzinfo: Europe/London, expected: America/Los_Angeles')},
    'input': datetime.datetime(2023, 1, 1, 0, 0, tzinfo=<DstTzInfo 'Europe/London' LMT-1 day, 23:59:00 STD>),
    'loc': (),
    'msg': 'Assertion failed, Invalid tzinfo: Europe/London, expected: America/Los_Angeles',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```

1. The `handler` function is what we call to validate the input with standard `pydantic` validation
2. We call the `handler` function to validate the input with standard `pydantic` validation in this wrap validator

We can also enforce UTC offset constraints in a similar way. Assuming we have a `lower_bound` and an `upper_bound`, we can create a custom validator to ensure our `datetime` has a UTC offset that is inclusive within the boundary we define:

```
import datetime as dt
from dataclasses import dataclass
from pprint import pprint
from typing import Annotated, Any, Callable

import pytz
from pydantic_core import CoreSchema, core_schema

from pydantic import GetCoreSchemaHandler, TypeAdapter, ValidationError

@dataclass(frozen=True)
class MyDatetimeValidator:
    lower_bound: int
    upper_bound: int

    def validate_tz_bounds(self, value: dt.datetime, handler: Callable):
        """Validate and test bounds"""
        assert value.utcoffset() is not None, 'UTC offset must exist'
        assert self.lower_bound <= self.upper_bound, 'Invalid bounds'

        result = handler(value)

        hours_offset = value.utcoffset().total_seconds() / 3600
        assert (
            self.lower_bound <= hours_offset <= self.upper_bound
        ), 'Value out of bounds'

        return result

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.validate_tz_bounds,
            handler(source_type),
        )

LA = 'America/Los_Angeles'  # UTC-7 or UTC-8
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(-10, -5)])
print(
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
)
#> 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    print(
        ta.validate_python(
            dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON))
        )
    )
except ValidationError as e:
    pprint(e.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Value out of bounds')},
    'input': datetime.datetime(2023, 1, 1, 0, 0, tzinfo=<DstTzInfo 'Europe/London' LMT-1 day, 23:59:00 STD>),
    'loc': (),
    'msg': 'Assertion failed, Value out of bounds',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```

```
import datetime as dt
from dataclasses import dataclass
from pprint import pprint
from typing import Annotated, Any
from collections.abc import Callable

import pytz
from pydantic_core import CoreSchema, core_schema

from pydantic import GetCoreSchemaHandler, TypeAdapter, ValidationError

@dataclass(frozen=True)
class MyDatetimeValidator:
    lower_bound: int
    upper_bound: int

    def validate_tz_bounds(self, value: dt.datetime, handler: Callable):
        """Validate and test bounds"""
        assert value.utcoffset() is not None, 'UTC offset must exist'
        assert self.lower_bound <= self.upper_bound, 'Invalid bounds'

        result = handler(value)

        hours_offset = value.utcoffset().total_seconds() / 3600
        assert (
            self.lower_bound <= hours_offset <= self.upper_bound
        ), 'Value out of bounds'

        return result

    def __get_pydantic_core_schema__(
        self,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            self.validate_tz_bounds,
            handler(source_type),
        )

LA = 'America/Los_Angeles'  # UTC-7 or UTC-8
ta = TypeAdapter(Annotated[dt.datetime, MyDatetimeValidator(-10, -5)])
print(
    ta.validate_python(dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LA)))
)
#> 2023-01-01 00:00:00-07:53

LONDON = 'Europe/London'
try:
    print(
        ta.validate_python(
            dt.datetime(2023, 1, 1, 0, 0, tzinfo=pytz.timezone(LONDON))
        )
    )
except ValidationError as e:
    pprint(e.errors(), width=100)
    """
    [{'ctx': {'error': AssertionError('Value out of bounds')},
    'input': datetime.datetime(2023, 1, 1, 0, 0, tzinfo=<DstTzInfo 'Europe/London' LMT-1 day, 23:59:00 STD>),
    'loc': (),
    'msg': 'Assertion failed, Value out of bounds',
    'type': 'assertion_error',
    'url': 'https://errors.pydantic.dev/2.8/v/assertion_error'}]
    """
```

## Validating Nested Model Fields¶

Here, we demonstrate two ways to validate a field of a nested model, where the validator utilizes data from the parent model.

In this example, we construct a validator that checks that each user's password is not in a list of forbidden passwords specified by the parent model.

One way to do this is to place a custom validator on the outer model:

```
from typing_extensions import Self

from pydantic import BaseModel, ValidationError, model_validator

class User(BaseModel):
    username: str
    password: str

class Organization(BaseModel):
    forbidden_passwords: list[str]
    users: list[User]

    @model_validator(mode='after')
    def validate_user_passwords(self) -> Self:
        """Check that user password is not in forbidden list. Raise a validation error if a forbidden password is encountered."""
        for user in self.users:
            current_pw = user.password
            if current_pw in self.forbidden_passwords:
                raise ValueError(
                    f'Password {current_pw} is forbidden. Please choose another password for user {user.username}.'
                )
        return self

data = {
    'forbidden_passwords': ['123'],
    'users': [
        {'username': 'Spartacat', 'password': '123'},
        {'username': 'Iceburgh', 'password': '87'},
    ],
}
try:
    org = Organization(**data)
except ValidationError as e:
    print(e)
    """
    1 validation error for Organization
      Value error, Password 123 is forbidden. Please choose another password for user Spartacat. [type=value_error, input_value={'forbidden_passwords': [...gh', 'password': '87'}]}, input_type=dict]
    """
```

```
from typing import Self

from pydantic import BaseModel, ValidationError, model_validator

class User(BaseModel):
    username: str
    password: str

class Organization(BaseModel):
    forbidden_passwords: list[str]
    users: list[User]

    @model_validator(mode='after')
    def validate_user_passwords(self) -> Self:
        """Check that user password is not in forbidden list. Raise a validation error if a forbidden password is encountered."""
        for user in self.users:
            current_pw = user.password
            if current_pw in self.forbidden_passwords:
                raise ValueError(
                    f'Password {current_pw} is forbidden. Please choose another password for user {user.username}.'
                )
        return self

data = {
    'forbidden_passwords': ['123'],
    'users': [
        {'username': 'Spartacat', 'password': '123'},
        {'username': 'Iceburgh', 'password': '87'},
    ],
}
try:
    org = Organization(**data)
except ValidationError as e:
    print(e)
    """
    1 validation error for Organization
      Value error, Password 123 is forbidden. Please choose another password for user Spartacat. [type=value_error, input_value={'forbidden_passwords': [...gh', 'password': '87'}]}, input_type=dict]
    """
```

Alternatively, a custom validator can be used in the nested model class (`User`), with the forbidden passwords data from the parent model being passed in via validation context.

Warning

The ability to mutate the context within a validator adds a lot of power to nested validation, but can also lead to confusing or hard-to-debug code. Use this approach at your own risk!

```python
from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator

class User(BaseModel):
    username: str
    password: str

    @field_validator('password', mode='after')
    @classmethod
    def validate_user_passwords(
        cls, password: str, info: ValidationInfo
    ) -> str:
        """Check that user password is not in forbidden list."""
        forbidden_passwords = (
            info.context.get('forbidden_passwords', []) if info.context else []
        )
        if password in forbidden_passwords:
            raise ValueError(f'Password {password} is forbidden.')
        return password

class Organization(BaseModel):
    forbidden_passwords: list[str]
    users: list[User]

    @field_validator('forbidden_passwords', mode='after')
    @classmethod
    def add_context(cls, v: list[str], info: ValidationInfo) -> list[str]:
        if info.context is not None:
            info.context.update({'forbidden_passwords': v})
        return v

data = {
    'forbidden_passwords': ['123'],
    'users': [
        {'username': 'Spartacat', 'password': '123'},
        {'username': 'Iceburgh', 'password': '87'},
    ],
}

try:
    org = Organization.model_validate(data, context={})
except ValidationError as e:
    print(e)
    """
    1 validation error for Organization
    users.0.password
      Value error, Password 123 is forbidden. [type=value_error, input_value='123', input_type=str]
    """
```

Note that if the context property is not included in `model_validate`, then `info.context` will be `None` and the forbidden passwords list will not get added to the context in the above implementation. As such, `validate_user_passwords` would not carry out the desired password validation.

More details about validation context can be found [here](https://docs.pydantic.dev/latest/concepts/validators/#validation-context).

---
title: "A Practical Guide to using Pydantic"
source: "https://medium.com/@marcnealer/a-practical-guide-to-using-pydantic-8aafa7feebf6"
author:
  - "[[Marc Nealer]]"
published: 2024-06-22
created: 2025-04-01
description: "When I started to experiment with FastAPI, I came across Pydantic. With FastAPI, you really have no choice. However, my initial thoughts on the library were not the best. Its has a somewhat steep…"
tags:
  - "clippings"
---
[

![Marc Nealer](https://miro.medium.com/v2/resize:fill:44:44/1*cI9XsBln8MnNAYuqheMDJA.jpeg)

](https://medium.com/@marcnealer?source=post_page---byline--8aafa7feebf6---------------------------------------)

![](https://miro.medium.com/v2/resize:fit:700/1*zjVYtfsd2vMoYIGeF6-_ug.png)

When I started to experiment with FastAPI, I came across Pydantic. With FastAPI, you really have no choice. However, my initial thoughts on the library were not the best. Its has a somewhat steep learning curve and there seems to be a lot of ways to do the same thing without any one saying, “oh use this route unless…”.

With that said, Pydantic is wonderful and such a powerful tool once you understand it. Its in my top 10 Python libraries.

![](https://miro.medium.com/v2/resize:fit:700/1*zjVYtfsd2vMoYIGeF6-_ug.png)

Before I continue, it should be noted that this document discusses Pydantic v2.\*. There are significant differences between version 1 and 2. I would also caution you on using ChatGTP or Gemini to help with coding Pydantic. Results given are a strange mix of version 1 and 2.

## So What is Pydantic

==Pydantic is Python Dataclasses with validation, serialization and data transformation functions.== So you can use Pydantic to check your data is valid. transform data into the shapes you need, and then serialize the results so they can be moved on to other applications.

## A REALLY Basic example

Lets say you have a function that expects a first and last name. you need to ensure both are there and that they are strings.

```
from pydantic import BaseModelclass MyFirstModel(BaseModel):
    first_name: str
    last_name: strvalidating = MyFirstModel(first_name="marc", last_name="nealer")
```

While this example is a little silly, it shows a couple of things. First off you can see Pydantic classes look almost the same as Python dataclasses. The second thing to note is that unlike a dataclass, Pydantic will check the values are strings and issue validation errors if they are not.

A point to note, is that validating by the type give, as shown here, is known as the default validation. Later we will discuss validation before and after this point.

## Lets get a little more complicated

When it comes to optional parameters, Pydantic handles then with no problem, but the typing might not be what you expect

```
from pydantic import BaseModel
from typing import Union, Optionalclass MySecondModel(BaseModel):
    first_name: str
    middle_name: Union[str, None] 
    title: Optional[str] 
    last_name: str
```

So if you use Union, with None as an option, then Pydantic is ok if the parameter is there or not. If you use Optional\[\], it expects the parameter to be sent, even if its blank. This notation might be what you expect, but I find it a little odd.

From this, you can see that we can use all the objects from the typing library and Pydantic will validate against them.

```
from pydantic import BaseModel
from typing import Union, List, Dict
from datetime import datetimeclass MyThirdModel(BaseModel):
    name: Dict[str: str]
    skills: List[str]
    holidays: List[Union[str, datetime]]
```

## Applying Default Values

so far we haven’t discussed what we would do if values are missing.

```
from pydantic import BaseModelclass DefaultsModel(BaseModel):
    first_name: str = "jane"
    middle_names: list = []
    last_name : str = "doe"
```

The seems kinda obvious. There is however a problem and that is with the definition of the list. If you code a model in this way, only one list object is created and its shared between all instances of this model. The same happens with dictionaries etc.

To resolve this, we need to introduce the Field Object.

```
from pydantic import BaseModel, Fieldclass DefaultsModel(BaseModel):
    first_name: str = "jane"
    middle_names: list = Field(default_factory=list)
    last_name: str = "doe"
```

Notice that a class or function is passed to the default factory and not a instance of such. This results in a new instance being created for all instances of the model.

If you have been looking at the Pydantic documentation, you would see the Field class being used in lots of different ways. However, the more I use Pydantic, the less I used the Field Object. It can do a lot of things, but it can also make life complicated. For the defaults and default factory, its the way to go. For the rest, well you will see what I do here.

## Nesting Models

I don’t have a lot of call to use nested Pydantic models, but I can see it being useful. Nesting is really simple

```
from pydantic import BaseModelclass NameModel(BaseModel):
    first_name: str
    last_name: str    class UserModel(BaseModel):
    username: str
    name: NameModel
```

## Custom Validation

While the default validation through types is great, we will always need to go beyond that. Pydantic has a number of different ways that you can add your own validation routines.

Before we start looking at any of these, we need to discuss the Before and After options. As I stated above, the tying validation is considered the default so when Pydantic adds custom validation on fields, its defined as before or after this default.

With model validation, which we will discuss a little later, the meaning is different. Before refers to validating before the object is initialized, and after, is when the object has been initialized and other validation has completed.

## Field Validation

We can define validation using the Field() object, but as we get more into Pydantic, overuse of the Field() object makes life difficult. We can also create validators using a decorator and stating the fields it is supposed to be applied to. What I prefer to use are the Annotated validators. They are neat and tidy, and easy to understand. Fellow programmers will be able to follow what your doing with ease.

```
from pydantic import BaseModel, BeforeValidator, ValidationError
import datetime
from typing import Annotateddef stamp2date(value):
    if not isinstance(value, float):
        raise ValidationError("incoming date must be a timestamp")
    try:
        res = datetime.datetime.fromtimestamp(value)
    except ValueError:
        raise ValidationError("Time stamp appears to be invalid")
    return resclass DateModel(BaseModel):
    dob: Annotated[datetime.datetime, BeforeValidator(stamp2date)]
```

The example is validating the data before the default validation. this is really useful as it gives us a chance to change and reformat the data, as well as validating. In this case I’m expecting a numerical time stamp to be passed. I validate for that and then convert the timestamp to a datetime object. The default validation is expecting a datetime object.

Pydantic also has AfterValidator and WrapValidator. The former runs after the default validator and the latter work like middleware, performing actions before and after. We can also apply multiple validator

```
from pydantic import BaseModel, BeforeValidator, AfterValidator, ValidationError
import datetime
from typing import Annotateddef one_year(value):
    if value < datetime.datetime.today() - datetime.timedelta(days=365):
        raise ValidationError("the date must be less than a year old")
    return value  def stamp2date(value):
    if not isinstance(value, float):
        raise ValidationError("incoming date must be a timestamp")
    try:
        res = datetime.datetime.fromtimestamp(value)
    except ValueError:
        raise ValidationError("Time stamp appears to be invalid")
    return resclass DateModel(BaseModel):
    dob: Annotated[datetime.datetime, BeforeValidator(stamp2date), AfterValidator(one_year)]
```

The majority of the time, I use the BeforeValidator. Transforming incoming data is a must, in many usecases. AfterValidator is great when you want to check that, while the value is of the right type, it has to meet other criteria. WrapValidator I haven’t used. I would like to hear from anyone who does, as I would like to understand the usecases for such.

Before we move on from this, I thought an example of where multiple types need to be an option. Or more to the point, where a parameter will be optional.

```
from pydantic import BaseModel, BeforeValidator, ValidationError, Field
import datetime
from typing import Annotateddef stamp2date(value):
    if not isinstance(value, float):
        raise ValidationError("incoming date must be a timestamp")
    try:
        res = datetime.datetime.fromtimestamp(value)
    except ValueError:
        raise ValidationError("Time stamp appears to be invalid")
    return resclass DateModel(BaseModel):
    dob: Annotated[Annotated[datetime.datetime, BeforeValidator(stamp2date)] | None, Field(default=None)]
```

## Model Validation

Lets take a simple usecase. We have three values, that are all going to be optional, but at least one of them has to be sent. Field validation only looks at each field on its own, so its no good here. This is where Model validation comes in.

```
from pydantic import BaseModel, model_validator, ValidationError
from typing import Union, Anyclass AllOptionalAfterModel(BaseModel):
    param1: Union[str, None] = None
    param2: Union[str, None] = None
    param3: Union[str, None] = None        @model_validator(mode="after")
    def there_must_be_one(self):
        if not (self.param1 or self.param2 or self.param3):
            raise ValidationError("One parameter must be specified")
        return selfclass AllOptionalBeforeModel(BaseModel):
    param1: Union[str, None] = None
    param2: Union[str, None] = None
    param3: Union[str, None] = None        @model_validator(mode="before")
    @classmethod
    def there_must_be_one(cls, data: Any):
        if not (data["param1"] or data["param2"] or data["param3"]):
            raise ValidationError("One parameter must be specified")
        return data
```

Above are two examples. The First is an After validation. You will notice that its marked mode=”after” and its passed the object as self. This is an important distinction.

The Before validation follows a very different route. First off, you can see the model\_validation decorator with mode=”before”. Then the classmethod decorator. Important. YOU NEED TO SPECIFY BOTH AND IN THIS ORDER.

I had some very odd error messages when I didn’t do this, so its an important point to note.

Next you will notice that the class and the data (parameters) passed to the class are both passed to the method as arguments. Validation is done on the data or passed values, which are usually passed on as a dictionary. The data object needs to be passed back at the end of the validation, thus showing you can use this method to alter the data, just like the BeforeValidator.

## Alias’s

Alias’s are important, especially if your dealing with incoming data and am performing transformations. We use alias’s to change the name of values, or to locate values when they are not passed as the field name.

Pydantic defines alias’s as Validation Alias’s (The name of the incoming value is not the same as the field), and Serialization Alias’s (changing the name when we serialize or output the data after validation).

The documentation goes into a lot of detail on defining the Alias’s using the Field() object, but there are issues with this. Defining defaults and Alias’s together doesn’t work. We can however define alias’s at the model level instead of at the field level.

```
from pydantic import AliasGenerator, BaseModel, ConfigDictclass Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: field_name.upper(),
            serialization_alias=lambda field_name: field_name.title(),
        )
    )    age: int
    height: float
    kind: strt = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
```

I took this example from the documentation, as its a bit on the simple side and not really of much use, but it does show how the field names can be transformed. A point to note here is that if you want to serialize the model using the serialization alias’s, you need to say so “by\_alias=True”.

Now lets get on with some more useful examples of using Alias’s using the AliasChoices and AliasPath objects.

## AliasChoices

Data being sent to you where a given value is given different field or column names, is really common. Ask a dozen people to send a list of names with first and last names in different columns, and I bet you get different column names!!

AliasChoices allows you to define a list of incoming value names that will match a given field.

```
from pydantic import BaseModel, ConfigDict, AliasGenerator, AliasChoicesaliases = {
    "first_name": AliasChoices("fname", "surname", "forename", "first_name"),
    "last_name": AliasChoices("lname", "family_name", "last_name")
}class FirstNameChoices(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: aliases.get(field_name, None)
        )
    )
    title: str
    first_name: str
    last_name: str
```

The code shown here allows you to define a dictionary where the key is the field name and the value is an AliasChoices object. Do note that I have included the actual field name in the list. You might be using this to transform and serialize data to be saved, and then want to read it back into the model for use. Thus the actual field name should be in the list.

## AliasPath

In most cases, incoming data is not flat, or comes in blobs of json, which are turned into dictionaries and then passed to your model. So how do we set a field to a value that is in a dictionary or list. Well that’s what AliasPath does.

```
from pydantic import BaseModel, ConfigDict, AliasGenerator, AliasPathaliases = {
    "first_name": AliasPath("name", "first_name"),
    "last_name": AliasPath("name",  "last_name")
}class FirstNameChoices(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: aliases.get(field_name, None)
        )
    )
    title: str
    first_name: str
    last_name: strobj = FirstNameChoices(**{"name":{"first_name": "marc", "last_name": "Nealer"},"title":"Master Of All"})
```

From the code above you can see first and last name are in a dictionary. I’ve used AliasPath to flatten the data pulling the values out of the dictionary, so all values are on the same level.

## Using AliasPath and AliasChoices

We can use both of these together.

```
from pydantic import BaseModel, ConfigDict, AliasGenerator, AliasPath, AliasChoicesaliases = {
    "first_name": AliasChoices("first_name", AliasPath("name", "first_name")),
    "last_name": AliasChoices("last_name", AliasPath("name",  "last_name"))
}class FirstNameChoices(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: aliases.get(field_name, None)
        )
    )
    title: str
    first_name: str
    last_name: strobj = FirstNameChoices(**{"name":{"first_name": "marc", "last_name": "Nealer"},"title":"Master Of All"})
```

## Final Thoughts

Pydantic is a Mega Brilliant library, but does suffer from having a lot of ways to do the same thing. To get to understanding and using the examples I’ve shown here, took a lot of work. I hope that using these, you can get stuck into Pydantic faster and with a far less work than I had to go through.

One last thing. Pydantic and AI services. Chat-gtp, Gemini etc give erratic answers to questions on Pydantic. Its like it can’t decide if its Pydantic V1 or V2 and just mixes then up. You even get “Pydantic can’t do that” to stuff it can. So best avoid them when using the library
