# SPDX-FileCopyrightText: 2022 spdx contributors
#
# SPDX-License-Identifier: Apache-2.0
from beartype.typing import List, Union

from spdx_tools.spdx.model import ExternalDocumentRef, File, Package, Snippet


def get_full_element_spdx_id(
    element: Union[Package, File, Snippet],
    document_namespace: str,
    external_document_refs: List[ExternalDocumentRef],
) -> str:
    """
    Returns the spdx_id of the element prefixed with the correct document namespace and,
    if the element is from an external document, sets the correct entry in the imports property.
    """
    if ":" not in element.spdx_id:
        return f"{document_namespace}#{element.spdx_id}"

    external_id, local_id = element.spdx_id.split(":")
    external_uri = None
    for entry in external_document_refs:
        if entry.document_ref_id == external_id:
            external_uri = entry.document_uri
            break

    if not external_uri:
        raise ValueError(f"external id {external_id} not found in external document references")

    return external_uri + "#" + local_id
