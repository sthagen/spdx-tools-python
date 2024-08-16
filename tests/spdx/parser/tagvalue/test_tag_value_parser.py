# Copyright (c) 2014 Ahmed H. Ismail
# SPDX-FileCopyrightText: 2023 spdx contributors
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from spdx_tools.spdx.constants import DOCUMENT_SPDX_ID
from spdx_tools.spdx.model import Relationship, RelationshipType, SpdxNoAssertion, SpdxNone
from spdx_tools.spdx.parser.error import SPDXParsingError
from spdx_tools.spdx.parser.tagvalue.parser import Parser
from tests.spdx.parser.tagvalue.test_creation_info_parser import DOCUMENT_STR


def test_parse_unknown_tag():
    parser = Parser()
    unknown_tag_str = "UnknownTag: This is an example for an unknown tag."

    with pytest.raises(SPDXParsingError, match="Unknown tag"):
        parser.parse(unknown_tag_str)


def test_building_contains_relationship():
    parser = Parser()
    document_str = "\n".join(
        [
            DOCUMENT_STR,
            "FileName: File without package",
            "SPDXID: SPDXRef-File",
            "FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
            "PackageName: Package with two files",
            "SPDXID: SPDXRef-Package-with-two-files",
            "PackageDownloadLocation: https://download.com",
            "FileName: File in package",
            "SPDXID: SPDXRef-File-in-Package",
            "FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
            "FileName: Second file in package",
            "SPDXID: SPDXRef-Second-File-in-Package",
            "FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
            "PackageName: Second package with file",
            "SPDXID: SPDXRef-Package-with-one-file",
            "PackageDownloadLocation: https://download.com",
            "FileName: File in package",
            "SPDXID: SPDXRef-File-in-different-Package",
            "FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
        ]
    )
    document = parser.parse(document_str)

    assert document.relationships == [
        Relationship("SPDXRef-Package-with-two-files", RelationshipType.CONTAINS, "SPDXRef-File-in-Package"),
        Relationship("SPDXRef-Package-with-two-files", RelationshipType.CONTAINS, "SPDXRef-Second-File-in-Package"),
        Relationship("SPDXRef-Package-with-one-file", RelationshipType.CONTAINS, "SPDXRef-File-in-different-Package"),
    ]


def test_build_contains_relationship_with_error():
    parser = Parser()
    file_spdx_ids = ["SPDXRef-File-in-Package", "SPDXRef-Second-File-in-Package"]
    document_str = "\n".join(
        [
            DOCUMENT_STR,
            "PackageName: Package with two files",
            "PackageDownloadLocation: https://download.com",
            "FileName: File in package",
            f"SPDXID: {file_spdx_ids[0]}",
            "FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
            "FileName: Second file in package",
            f"SPDXID: {file_spdx_ids[1]}",
            "FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
        ]
    )
    with pytest.raises(SPDXParsingError) as err:
        parser.parse(document_str)
    for file_spdx_id in file_spdx_ids:
        assert (
            f"Error while building contains relationship for file {file_spdx_id}, preceding package was not "
            "parsed successfully." in err.value.get_messages()
        )


def test_document_with_mixed_values():
    parser = Parser()
    document_str = "\n".join(
        [
            f"SPDXID:{DOCUMENT_SPDX_ID}",
            "FileName: File without package",
            "SPDXID: SPDXRef-File",
            "PackageDownloadLocation: https://download.com",
            "FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
        ]
    )

    with pytest.raises(SPDXParsingError) as err:
        parser.parse(document_str)

    assert err.value.get_messages() == [
        "Element Package is not the current element in scope, probably the expected "
        "tag to start the element (PackageName) is missing. Line: 4"
    ]


def test_faulty_license_expression():
    parser = Parser()
    document_str = "\n".join(
        [
            f"SPDXID:{DOCUMENT_SPDX_ID}",
            "FileName: File with faulty license expression",
            "SPDXID: SPDXRef-File",
            "FileChecksum: SHA1: d6a770ba38583ed4bb4525bd96e50461655d2759",
            "LicenseConcluded: LicenseRef-foo/bar",
            "PackageName: Package with faulty license expression",
            "SPDXID: SPDXRef-Package",
            "PackageDownloadLocation: www.download.com",
            "PackageLicenseConcluded: LicenseRef-bar/foo",
            "SnippetSPDXID: SPDXRef-Snippet",
            "SnippetName: Snippet with faulty license expression",
            "SnippetLicenseConcluded: LicenseRef-foo/foo",
        ]
    )

    with pytest.raises(SPDXParsingError) as err:
        parser.parse(document_str)

    assert err.value.get_messages() == [
        'Error while parsing File: ["Error while parsing license expression: '
        "LicenseRef-foo/bar: Invalid license key: the valid characters are: letters "
        "and numbers, underscore, dot, colon or hyphen signs and spaces: "
        "'LicenseRef-foo/bar'\"]",
        'Error while parsing Package: ["Error while parsing license expression: '
        "LicenseRef-bar/foo: Invalid license key: the valid characters are: letters "
        "and numbers, underscore, dot, colon or hyphen signs and spaces: "
        "'LicenseRef-bar/foo'\"]",
        'Error while parsing Snippet: ["Error while parsing license expression: '
        "LicenseRef-foo/foo: Invalid license key: the valid characters are: letters "
        "and numbers, underscore, dot, colon or hyphen signs and spaces: "
        "'LicenseRef-foo/foo'\"]",
    ]


def test_parse_none_or_no_assertion_as_text():
    parser = Parser()
    document_str = "\n".join(
        [
            DOCUMENT_STR,
            "PackageName: Test",
            "SPDXID: SPDXRef-Package",
            "PackageDownloadLocation: http://example.com/test",
            "FilesAnalyzed: true",
            "PackageSummary: NONE",
            "PackageSourceInfo: NOASSERTION",
            "PackageLicenseConcluded: NONE",
            "PackageLicenseDeclared: NOASSERTION",
        ]
    )
    document = parser.parse(document_str)
    assert document is not None
    package = document.packages[0]
    assert package.name == "Test"
    assert package.spdx_id == "SPDXRef-Package"
    assert package.source_info == "NOASSERTION"
    assert package.summary == "NONE"
    assert package.license_concluded == SpdxNone()
    assert package.license_declared == SpdxNoAssertion()
