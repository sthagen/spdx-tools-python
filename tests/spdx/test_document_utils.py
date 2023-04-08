# SPDX-FileCopyrightText: 2023 spdx contributors
#
# SPDX-License-Identifier: Apache-2.0
from unittest import TestCase

import pytest

from spdx.document_utils import get_contained_spdx_element_ids, get_contained_spdx_elements, get_element_from_spdx_id
from tests.spdx.fixtures import document_fixture, file_fixture, package_fixture, snippet_fixture


@pytest.fixture
def variables():
    return document_fixture(), package_fixture(), file_fixture(), snippet_fixture()


def test_contained_element_ids(variables):
    document, package, file, snippet = variables
    element_ids = get_contained_spdx_element_ids(document)
    TestCase().assertCountEqual(element_ids, [package.spdx_id, file.spdx_id, snippet.spdx_id])


def test_get_element_from_spdx_id(variables):
    document, package, file, snippet = variables
    assert get_element_from_spdx_id(document, package.spdx_id) == package
    assert get_element_from_spdx_id(document, file.spdx_id) == file
    assert get_element_from_spdx_id(document, snippet.spdx_id) == snippet
    assert get_element_from_spdx_id(document, "unknown_id") is None


def test_get_contained_spdx_elements(variables):
    document, package, file, snippet = variables
    contained_elements = get_contained_spdx_elements(document)
    assert contained_elements[package.spdx_id] == package
    assert contained_elements[file.spdx_id] == file
    assert contained_elements[snippet.spdx_id] == snippet
