# Python library to parse, validate and create SPDX documents

CI status (Linux, macOS and Windows): [![Install and Test][1]][2]

[1]: https://github.com/spdx/tools-python/actions/workflows/install_and_test.yml/badge.svg

[2]: https://github.com/spdx/tools-python/actions/workflows/install_and_test.yml


# Current state, please read!

This repository was subject to a major refactoring recently to get ready for the upcoming SPDX v3.0 release.
Therefore, we'd like to encourage you to post any and all issues you find at https://github.com/spdx/tools-python/issues.  
If you are looking for the source code of the [current PyPI release](https://pypi.python.org/pypi/spdx-tools), check out
the [v0.7 branch](https://github.com/spdx/tools-python/tree/version/v0.7).
Note, though, that this will only receive bug fixes but no new features.

We encourage you to use the new, refactored version (on the main branch) if you
- want to use the soon-to-be released SPDX v3.0 in the future
- want to perform full validation of your SPDX documents against the v2.2 and v2.3 specification
- want to use the RDF format of SPDX with all v2.3 features.

If you are planning to migrate from v0.7.x of these tools,
please have a look at the [migration guide](https://github.com/spdx/tools-python/wiki/How-to-migrate-from-0.7-to-0.8).

# Information

This library implements SPDX parsers, convertors, validators and handlers in Python.

- Home: https://github.com/spdx/tools-python
- Issues: https://github.com/spdx/tools-python/issues
- PyPI: https://pypi.python.org/pypi/spdx-tools


# License

[Apache-2.0](LICENSE)

# Features

* API to create and manipulate SPDX v2.2 and v2.3 documents
* Parse, convert, create and validate SPDX files
* supported formats: Tag/Value, RDF, JSON, YAML, XML
* visualize the structure of a SPDX document by creating an `AGraph`. Note: This is an optional feature and requires 
additional installation of optional dependencies

# Planned features

* up-to-date support of SPDX v3.0 as soon as it is released

# Installation

As always you should work in a virtualenv (venv). You can install a local clone
of this repo with `yourenv/bin/pip install .` or install it from PyPI with
`yourenv/bin/pip install spdx-tools`. Note that on Windows it would be `Scripts`
instead of `bin`.

# How to use

## Command-line usage

1. **PARSING/VALIDATING** (for parsing any format):

* Use `pyspdxtools -i <filename>` where `<filename>` is the location of the file. The input format is inferred automatically from the file ending.

* If you are using a source distribution, try running:  
  `pyspdxtools -i tests/data/SPDXJSONExample-v2.3.spdx.json`

2. **CONVERTING** (for converting one format to another):

* Use `pyspdxtools -i <input_file> -o <output_file>` where `<input_file>` is the location of the file to be converted
  and `<output_file>` is the location of the output file. The input and output formats are inferred automatically from the file endings.

* If you are using a source distribution, try running:  
  `pyspdxtools -i tests/data/SPDXJSONExample-v2.3.spdx.json -o output.tag` 

* If you want to skip the validation process, provide the `--novalidation` flag, like so:  
  `pyspdxtools -i tests/data/SPDXJSONExample-v2.3.spdx.json -o output.tag --novalidation`  
  (use this with caution: note that undetected invalid documents may lead to unexpected behavior of the tool)
  
* For help use `pyspdxtools --help`

3. **GRAPH GENERATION** (optional feature)

* This feature generates a graph representing all elements in the SPDX document and their connections based on the provided
  relationships. The graph can be rendered to a picture. Below is an example for the file `tests/data/SPDXJSONExample-v2.3.spdx.json`:
![SPDXJSONExample-v2.3.spdx.png](assets/SPDXJSONExample-v2.3.spdx.png)
* Make sure you install the optional dependencies `networkx` and `pygraphviz`. To do so run `pip install ".[graph_generation]"`.
* Use `pyspdxtools -i <input_file> --graph -o <output_file>` where `<output_file>` is an output file name with valid format for `pygraphviz` (check 
  the documentation [here](https://pygraphviz.github.io/documentation/stable/reference/agraph.html#pygraphviz.AGraph.draw)). 
* If you are using a source distribution, try running
  `pyspdxtools -i tests/data/SPDXJSONExample-v2.3.spdx.json --graph -o SPDXJSONExample-v2.3.spdx.png` to generate 
  a png with an overview of the structure of the example file.  

## Library usage
1. **DATA MODEL**
  * The `spdx_tools.spdx.model` package constitutes the internal SPDX v2.3 data model (v2.2 is simply a subset of this). All relevant classes for SPDX document creation are exposed in the `__init__.py` found [here](src%2Fspdx_tools%2Fspdx%2Fmodel%2F__init__.py).
  * SPDX objects are implemented via `@dataclass_with_properties`, a custom extension of `@dataclass`.
    * Each class starts with a list of its properties and their possible types. When no default value is provided, the property is mandatory and must be set during initialization.
    * Using the type hints, type checking is enforced when initializing a new instance or setting/getting a property on an instance
      (wrong types will raise `ConstructorTypeError` or `TypeError`, respectively). This makes it easy to catch invalid properties early and only construct valid documents.
    * Note: in-place manipulations like `list.append(item)` will circumvent the type checking (a `TypeError` will still be raised when reading `list` again). We recommend using `list = list + [item]` instead.
  * The main entry point of an SPDX document is the `Document` class from the [document.py](src%2Fspdx_tools%2Fspdx%2Fmodel%2Fdocument.py) module, which links to all other classes.
  * For license handling, the [license_expression](https://github.com/nexB/license-expression) library is used.
  * Note on `documentDescribes` and `hasFiles`: These fields will be converted to relationships in the internal data model. As they are deprecated, these fields will not be written in the output.
2. **PARSING**
  * Use `parse_file(file_name)` from the `parse_anything.py` module to parse an arbitrary file with one of the supported file endings.
  * Successful parsing will return a `Document` instance. Unsuccessful parsing will raise `SPDXParsingError` with a list of all encountered problems.
3. **VALIDATING**
  * Use `validate_full_spdx_document(document)` to validate an instance of the `Document` class.
  * This will return a list of `ValidationMessage` objects, each consisting of a String describing the invalidity and a `ValidationContext` to pinpoint the source of the validation error.
  * Validation depends on the SPDX version of the document. Note that only versions `SPDX-2.2` and `SPDX-2.3` are supported by this tool.
4. **WRITING**
  * Use `write_file(document, file_name)` from the `write_anything.py` module to write a `Document` instance to the specified file.
    The serialization format is determined from the filename ending.
  * Validation is performed per default prior to the writing process, which is cancelled if the document is invalid. You can skip the validation via `write_file(document, file_name, validate=False)`.
    Caution: Only valid documents can be serialized reliably; serialization of invalid documents is not supported.

## Example
Here are some examples of possible use cases to quickly get you started with the spdx-tools.
If you want a more comprehensive example about how to create an SPDX document from scratch, have a look [here](examples%2Fspdx2_document_from_scratch.py).
```python
import logging

from license_expression import get_spdx_licensing

from spdx_tools.spdx.model import (Checksum, ChecksumAlgorithm, File, 
                                   FileType, Relationship, RelationshipType)
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.validation.document_validator import validate_full_spdx_document
from spdx_tools.spdx.writer.write_anything import write_file

# read in an SPDX document from a file
document = parse_file("spdx_document.json")

# change the document's name
document.creation_info.name = "new document name"

# define a file and a DESCRIBES relationship between the file and the document
checksum = Checksum(ChecksumAlgorithm.SHA1, "71c4025dd9897b364f3ebbb42c484ff43d00791c")

file = File(name="./fileName.py", spdx_id="SPDXRef-File", checksums=[checksum], 
            file_types=[FileType.TEXT], 
            license_concluded=get_spdx_licensing().parse("MIT and GPL-2.0"),
            license_comment="licenseComment", copyright_text="copyrightText")

relationship = Relationship("SPDXRef-DOCUMENT", RelationshipType.DESCRIBES, "SPDXRef-File")

# add the file and the relationship to the document 
# (note that we do not use "document.files.append(file)" as that would circumvent the type checking)
document.files = document.files + [file]
document.relationships = document.relationships + [relationship]

# validate the edited document and log the validation messages
# (depending on your use case, you might also want to utilize the validation_message.context)
validation_messages = validate_full_spdx_document(document)
for validation_message in validation_messages:
    logging.warning(validation_message.validation_message)

# if there are no validation messages, the document is valid 
# and we can safely serialize it without validating again
if not validation_messages:
    write_file(document, "new_spdx_document.rdf", validate=False)
```

# Dependencies

* PyYAML: https://pypi.org/project/PyYAML/ for handling YAML.
* xmltodict: https://pypi.org/project/xmltodict/ for handling XML.
* rdflib: https://pypi.python.org/pypi/rdflib/ for handling RDF.
* ply: https://pypi.org/project/ply/ for handling tag-value.
* click: https://pypi.org/project/click/ for creating the CLI interface.
* typeguard: https://pypi.org/project/typeguard/ for type checking.
* uritools: https://pypi.org/project/uritools/ for validation of URIs.
* license-expression: https://pypi.org/project/license-expression/ for handling SPDX license expressions.

# Support

* Submit issues, questions or feedback at https://github.com/spdx/tools-python/issues
* Join the chat at https://gitter.im/spdx-org/Lobby
* Join the discussion on https://lists.spdx.org/g/spdx-tech and
  https://spdx.dev/participate/tech/

# Contributing

Contributions are very welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for instructions on how to contribute to the
codebase.

# History

This is the result of an initial GSoC contribution by @[ah450](https://github.com/ah450)
(or https://github.com/a-h-i) and is maintained by a community of SPDX adopters and enthusiasts.
In order to prepare for the release of SPDX v3.0, the repository has undergone a major refactoring during the time from 11/2022 to 03/2023.
