DTO rationale
=============

.. admonition:: What particular problem does DTO solve in Litestar ?

    DTOs as Litestar implements them provide an enormous amount of flexibility when it comes to data modelling. Their most value is probably derived behind the scences, without a user explicitly creating a DTO.

    The SQLAlchemy integration would be an example.

    You can directly return a SQLAlchemy mapped class from a handler, and Litestar will know how to serialise it.

    Behind the scenes, this is powered by DTOs.

    The general idea is that they provide a generic interface to transform structured data from one form into structured data in a different form, and that the input and output data structure don't matter, as long as they can be mapped to a "receives properties as keyword arguments" / "provides attribute or mapping style access to properties" style object.

    In practice this means you can easily e.g. map from:

    - JSON -> msgspec
    - JSON -> Pydantic
    - SQLAlchemy -> msgspec -> JSON
    - dict -> pydantic
    - attrs -> msgspec -> JSON

    or whatever way you can think of...

    The DTO interface Litestar surfaces is basically just a convenient interface to hook into that process, allowing to perform multiple transformation steps at once.
    For example, if you want to map from SQLAlchemy > JSON, while also renaming some attributes, it's more efficient to do that in one step than going from SQLA > dict > drop attrs > JSON

    Another benefit of this is declarative transformations.

    If you have a different representation of your data on the wire than in your DB, without such a mechanism, you'd have to somehow manually map between the two.

    With Litestar's DTOs, you can declare how the data should be mapped, and the transformation will happen automatically.

    That's particularly useful for things like renaming fields, dropping fields, or e.g. making all fields optional (provided by the partial=True switch).

    Where things get *really exciting* though is, at least I think so, that all of this is completely transparent to the OpenAPI schema, which means all the transformation steps applied to your data are taken into account in the final schema.

    The only other way to achieve this is to manually transform the input > output, output > input models, and only surface the respective public models to the parts concerned with generating the schema (this is what all - as far as I'm aware - other frameworks in the Python space that provide similar auto-OpenAPI schema generation require you to do 🙂).

    Performance is yet another thing. DTOs use some metaprogramming voodoo to generate efficient transfer functions, that you definitely wouldn't (or something hardly could) write by hand, to achieve quite a low overhead.
