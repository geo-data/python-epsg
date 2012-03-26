# TODO

- Make the `discriminator` and foreign key id attributes private
- Add a `@validates` decorator to numeric attributes to perform on the
  fly conversions from strings.
- The object model was created for the general requirements of a
  specific project: it is not the result of implementing the GML
  schema! This means that some attributes/elements may be missing but
  it should otherwise approximate the GML schema.
- The following EPSG GML elements are still to be mapped to the python
  object model:

    BaseUnit
    CompoundCRS
    ConcatenatedOperation
    ConventionalUnit
    Conversion
    DerivedUnit
    OperationMethod
    OperationParameter
    Transformation
    epsg:ChangeRequest
    epsg:Deprecation
    epsg:NamingSystem
    epsg:Supersession
    epsg:VersionHistory
