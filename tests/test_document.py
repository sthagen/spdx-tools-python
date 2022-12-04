# Copyright (c) 2014 Ahmed H. Ismail
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest import TestCase

from spdx.checksum import Checksum, ChecksumAlgorithm
from spdx.config import LICENSE_MAP, EXCEPTION_MAP
from spdx.creationinfo import Tool
from spdx.document import Document, ExternalDocumentRef
from spdx.license import License
from spdx.file import File, FileType
from spdx.package import Package, PackagePurpose
from spdx.parsers.loggers import ErrorMessages
from spdx.relationship import Relationship, RelationshipType
from spdx.utils import NoAssert
from spdx.version import Version

from tests import utils_test


class TestVersion(TestCase):
    maxDiff = None

    def test_creation(self):
        v = Version(major=2, minor=1)
        assert v.major == 2
        assert v.minor == 1

    def test_comparison(self):
        v1 = Version(major=1, minor=2)
        v2 = Version(major=2, minor=1)
        assert v1 != v2
        assert v1 < v2
        assert v1 <= v2
        assert v2 > v1
        assert v2 >= v1
        v3 = Version(major=1, minor=2)
        assert v3 == v1
        assert not v1 < v3
        assert v1 <= v3


class TestDocument(TestCase):
    maxDiff = None

    def test_creation(self):
        document = Document(
            version=Version(major=2, minor=1),
            data_license=License(full_name='Academic Free License v1.1',
                                identifier='AFL-1.1')
        )
        document.add_ext_document_reference(
            ExternalDocumentRef('DocumentRef-spdx-tool-2.1',
                                'https://spdx.org/spdxdocs/spdx-tools-v2.1-3F2504E0-4F89-41D3-9A0C-0305E82C3301',
                                Checksum(ChecksumAlgorithm.SHA1, 'SOME-SHA1'))
        )
        assert document.comment is None
        assert document.version == Version(2, 1)
        assert document.data_license.identifier == 'AFL-1.1'
        assert document.ext_document_references[-1].external_document_id == 'DocumentRef-spdx-tool-2.1'
        assert document.ext_document_references[-1].spdx_document_uri == 'https://spdx.org/spdxdocs/spdx-tools-v2.1-3F2504E0-4F89-41D3-9A0C-0305E82C3301'
        assert document.ext_document_references[-1].checksum.identifier.name == 'SHA1'
        assert document.ext_document_references[-1].checksum.value == 'SOME-SHA1'

    def test_document_validate_failures_returns_informative_messages(self):
        doc = Document(Version(2, 1), License.from_identifier('CC0-1.0'),
                       'Sample_Document-V2.1', spdx_id='SPDXRef-DOCUMENT',
                       namespace='https://spdx.org/spdxdocs/spdx-example-444504E0-4F89-41D3-9A0C-0305E82C3301')
        pack = doc.package = Package('some/path', NoAssert())
        pack.set_checksum(Checksum(ChecksumAlgorithm.SHA256, 'SOME-SHA256'))
        file1 = File('./some/path/tofile')
        file1.name = './some/path/tofile'
        file1.spdx_id = 'SPDXRef-File'
        file1.set_checksum(Checksum(ChecksumAlgorithm.SHA1, 'SOME-SHA1'))
        lic1 = License.from_identifier('LGPL-2.1-only')
        file1.add_lics(lic1)
        pack.add_lics_from_file(lic1)
        messages = ErrorMessages()
        messages = doc.validate(messages)
        expected = ['Sample_Document-V2.1: Creation info missing created date.',
                    'Sample_Document-V2.1: No creators defined, must have at least one.',
                    'Sample_Document-V2.1: some/path: Package download_location can not be None.']
        assert sorted(expected) == sorted(messages)

    def test_document_is_valid_when_using_or_later_licenses(self):
        doc = Document(Version(2, 1), License.from_identifier('CC0-1.0'),
                       'Sample_Document-V2.1', spdx_id='SPDXRef-DOCUMENT',
                       namespace='https://spdx.org/spdxdocs/spdx-example-444504E0-4F89-41D3-9A0C-0305E82C3301')
        doc.creation_info.add_creator(Tool('ScanCode'))
        doc.creation_info.set_created_now()

        package = doc.package = Package(name='some/path', download_location=NoAssert())
        package.spdx_id = 'SPDXRef-Package'
        package.cr_text = 'Some copyright'
        package.set_checksum(Checksum(ChecksumAlgorithm.SHA1, 'SOME-SHA1'))
        package.verif_code = 'SOME code'
        package.license_declared = NoAssert()
        package.conc_lics = NoAssert()

        file1 = File('./some/path/tofile')
        file1.name = './some/path/tofile'
        file1.spdx_id = 'SPDXRef-File'
        file1.file_types = [FileType.OTHER]
        file1.set_checksum(Checksum(ChecksumAlgorithm.SHA1, 'SOME-SHA1'))
        file1.conc_lics = NoAssert()
        file1.copyright = NoAssert()

        lic1 = License.from_identifier('LGPL-2.1-or-later')
        file1.add_lics(lic1)

        package.add_lics_from_file(lic1)
        doc.add_file(file1)
        relationship = create_relationship(package.spdx_id, RelationshipType.CONTAINS, file1.spdx_id)
        doc.add_relationship(relationship)
        messages = ErrorMessages()
        messages = doc.validate(messages)
        assert not messages

    def test_document_multiple_packages(self):
        doc = Document(Version(2, 1), License.from_identifier('CC0-1.0'),
                       'Sample_Document-V2.1', spdx_id='SPDXRef-DOCUMENT',
                       namespace='https://spdx.org/spdxdocs/spdx-example-444504E0-4F89-41D3-9A0C-0305E82C3301')
        doc.creation_info.add_creator(Tool('ScanCode'))
        doc.creation_info.set_created_now()

        package1 = Package(name='some/path1', download_location=NoAssert())
        package1.spdx_id = 'SPDXRef-Package1'
        package1.cr_text = 'Some copyright'
        package1.files_verified = False
        package1.license_declared = NoAssert()
        package1.conc_lics = NoAssert()
        doc.add_package(package1)

        package2 = Package(name='some/path2', download_location=NoAssert())
        package2.spdx_id = 'SPDXRef-Package2'
        package2.cr_text = 'Some copyright'
        package2.files_verified = False
        package2.license_declared = NoAssert()
        package2.conc_lics = NoAssert()
        doc.add_package(package2)

        assert len(doc.packages) == 2

    def test_document_without_packages(self):
        doc = Document(Version(2, 1), License.from_identifier("CC0-1.0"),
                       'Sample_Document_V2.1', spdx_id='SPDXRef-DOCUMENT',
                       namespace='https://spdx.org/spdxdocs/spdx-example-444504E0-4F89-41D3-9A0C-0305E82C3301')
        doc.creation_info.add_creator(Tool('ScanCode'))
        doc.creation_info.set_created_now()

        messages = doc.validate()
        assert len(messages.messages) == 0

class TestWriters(TestCase):
    maxDiff = None

    def _get_lgpl_doc(self, or_later=False):
        doc = Document(Version(2, 1), License.from_identifier('CC0-1.0'),
                       'Sample_Document-V2.1', spdx_id='SPDXRef-DOCUMENT',
                       namespace='https://spdx.org/spdxdocs/spdx-example-444504E0-4F89-41D3-9A0C-0305E82C3301')
        doc.creation_info.add_creator(Tool('ScanCode'))
        doc.creation_info.set_created_now()

        package = doc.package = Package(name='some/path', download_location=NoAssert())
        package.spdx_id = 'SPDXRef-Package'
        package.cr_text = 'Some copyright'
        package.verif_code = 'SOME code'
        package.set_checksum(Checksum(ChecksumAlgorithm.SHA1, 'SOME-SHA1'))
        package.set_checksum(Checksum(ChecksumAlgorithm.SHA256, 'SOME-SHA256'))
        package.license_declared = NoAssert()
        package.conc_lics = NoAssert()
        package.primary_package_purpose = PackagePurpose.FILE
        package.release_date = datetime(2021, 1, 1, 12, 0, 0)
        package.built_date = datetime(2021, 1, 1, 12, 0, 0)
        package.valid_until_date = datetime(2022, 1, 1, 12, 0, 0)


        file1 = File('./some/path/tofile')
        file1.name = './some/path/tofile'
        file1.spdx_id = 'SPDXRef-File'
        file1.set_checksum(Checksum(ChecksumAlgorithm.SHA1, 'SOME-SHA1'))
        file1.set_checksum(Checksum(ChecksumAlgorithm.SHA256, 'SOME-SHA256'))
        file1.conc_lics = NoAssert()
        file1.copyright = NoAssert()
        file1.file_types = [FileType.OTHER, FileType.SOURCE]

        lic1 = License.from_identifier('LGPL-2.1-only')
        if or_later:
            lic1 = License.from_identifier('LGPL-2.1-or-later')

        file1.add_lics(lic1)
        doc.add_file(file1)

        package.add_lics_from_file(lic1)
        relationship = create_relationship(package.spdx_id, RelationshipType.CONTAINS, file1.spdx_id)
        doc.add_relationship(relationship)
        relationship = create_relationship(doc.spdx_id, RelationshipType.DESCRIBES, package.spdx_id)
        doc.add_relationship(relationship)
        return doc

    def _get_lgpl_multi_package_doc(self, or_later=False):
        doc = Document(Version(2, 1), License.from_identifier('CC0-1.0'),
                       'Sample_Document-V2.1', spdx_id='SPDXRef-DOCUMENT',
                       namespace='https://spdx.org/spdxdocs/spdx-example-444504E0-4F89-41D3-9A0C-0305E82C3301')
        doc.creation_info.add_creator(Tool('ScanCode'))
        doc.creation_info.set_created_now()

        # This package does not have files analyzed
        package1 = Package(name='some/path1', download_location=NoAssert())
        package1.spdx_id = 'SPDXRef-Package1'
        package1.cr_text = 'Some copyright'
        package1.files_analyzed = False
        package1.license_declared = NoAssert()
        package1.conc_lics = NoAssert()
        doc.add_package(package1)

        # This one does, which is the default
        package2 = Package(name='some/path2', download_location=NoAssert())
        package2.spdx_id = 'SPDXRef-Package2'
        package2.cr_text = 'Some copyright'
        package2.license_declared = NoAssert()
        package2.conc_lics = NoAssert()
        package2.verif_code = 'SOME code'

        # This one does, but per recommendation, we choose to make the
        # verification code optional in this library
        package3 = Package(name='some/path3', download_location=NoAssert())
        package3.spdx_id = 'SPDXRef-Package3'
        package3.cr_text = 'Some copyright'
        package3.license_declared = NoAssert()
        package3.conc_lics = NoAssert()

        file1 = File('./some/path/tofile')
        file1.name = './some/path/tofile'
        file1.spdx_id = 'SPDXRef-File'
        file1.set_checksum(Checksum(ChecksumAlgorithm.SHA1, 'SOME-SHA1'))
        file1.conc_lics = NoAssert()
        file1.copyright = NoAssert()

        lic1 = License.from_identifier('LGPL-2.1-only')
        if or_later:
            lic1 = License.from_identifier('LGPL-2.1-or-later')

        file1.add_lics(lic1)

        package2.add_lics_from_file(lic1)
        package3.add_lics_from_file(lic1)

        doc.add_package(package2)
        doc.add_package(package3)
        doc.add_file(file1)

        relationship = create_relationship(doc.spdx_id, RelationshipType.DESCRIBES, package1.spdx_id)
        doc.add_relationship(relationship)
        relationship = create_relationship(doc.spdx_id, RelationshipType.DESCRIBES, package2.spdx_id)
        doc.add_relationship(relationship)
        relationship = create_relationship(doc.spdx_id, RelationshipType.DESCRIBES, package3.spdx_id)
        doc.add_relationship(relationship)
        relationship = create_relationship(package2.spdx_id, RelationshipType.CONTAINS, file1.spdx_id)
        doc.add_relationship(relationship)
        relationship = create_relationship(package3.spdx_id, RelationshipType.CONTAINS, file1.spdx_id)
        doc.add_relationship(relationship)

        return doc

    def test_write_document_rdf_with_validate(self):
        from spdx.writers.rdf import write_document
        doc = self._get_lgpl_doc()
        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple.rdf')
            with open(result_file, 'wb') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/rdf-simple.json',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_rdf_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_rdf_with_or_later_with_validate(self):
        from spdx.writers.rdf import write_document
        doc = self._get_lgpl_doc(or_later=True)

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple-plus.rdf')

            # test proper!
            with open(result_file, 'wb') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/rdf-simple-plus.json',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_rdf_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_tv_with_validate(self):
        from spdx.writers.tagvalue import write_document
        doc = self._get_lgpl_doc()

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple.tv')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/tv-simple.tv',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_tv_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_tv_with_or_later_with_validate(self):
        from spdx.writers.tagvalue import write_document

        doc = self._get_lgpl_doc(or_later=True)

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple-plus.tv')

            # test proper!
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/tv-simple-plus.tv',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_tv_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_json_with_validate(self):
        from spdx.writers.json import write_document
        doc = self._get_lgpl_doc()

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple.json')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/json-simple.json',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_json_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_json_with_or_later_with_validate(self):
        from spdx.writers.json import write_document
        doc = self._get_lgpl_doc(or_later=True)

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple-plus.json')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/json-simple-plus.json',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_json_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_json_multi_package_with_validate(self):
        from spdx.writers.json import write_document
        doc = self._get_lgpl_multi_package_doc(or_later=True)

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple-multi-package.json')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/json-simple-multi-package.json',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_json_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


    def test_write_document_yaml_with_validate(self):
        from spdx.writers.yaml import write_document
        doc = self._get_lgpl_doc()

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple.yaml')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/yaml-simple.yaml',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_yaml_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_yaml_with_or_later_with_validate(self):
        from spdx.writers.yaml import write_document
        doc = self._get_lgpl_doc(or_later=True)

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple-plus.yaml')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/yaml-simple-plus.yaml',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_yaml_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_yaml_multi_package_with_validate(self):
        from spdx.writers.yaml import write_document
        doc = self._get_lgpl_multi_package_doc(or_later=True)

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple-multi-package.yaml')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/yaml-simple-multi-package.yaml',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_yaml_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_xml_with_validate(self):
        from spdx.writers.xml import write_document
        doc = self._get_lgpl_doc()

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple.xml')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/xml-simple.xml',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_xml_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_xml_with_or_later_with_validate(self):
        from spdx.writers.xml import write_document
        doc = self._get_lgpl_doc(or_later=True)

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple-plus.xml')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/xml-simple-plus.xml',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_xml_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_xml_multi_package_with_validate(self):
        from spdx.writers.xml import write_document
        doc = self._get_lgpl_multi_package_doc(or_later=True)

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple-multi-package.xml')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=True)

            expected_file = utils_test.get_test_loc(
                'doc_write/xml-simple-multi-package.xml',
                test_data_dir=utils_test.test_data_dir)

            utils_test.check_xml_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _get_mini_doc(self,):
        doc = Document(Version(2, 1), License.from_identifier('CC0-1.0'))
        doc.creation_info.set_created_now()

        return doc

    def test_write_document_tv_mini(self):
        from spdx.writers.tagvalue import write_document
        doc = self._get_mini_doc()

        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple.tv')
            with open(result_file, 'w') as output:
                write_document(doc, output, validate=False)
            expected_file = utils_test.get_test_loc('doc_write/tv-mini.tv')
            utils_test.check_tv_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_write_document_rdf_mini(self):
        from spdx.writers.rdf import write_document
        doc = self._get_mini_doc()
        temp_dir = ''
        try:
            temp_dir = tempfile.mkdtemp(prefix='test_spdx')
            result_file = os.path.join(temp_dir, 'spdx-simple.rdf')
            with open(result_file, 'wb') as output:
                write_document(doc, output, validate=False)
            expected_file = utils_test.get_test_loc('doc_write/rdf-mini.json')
            utils_test.check_rdf_scan(expected_file, result_file, regen=False)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def create_relationship(spdx_element_id: str, relationship_type: RelationshipType, related_spdx_element: str) -> Relationship:
    return Relationship(spdx_element_id + " " + relationship_type.name + " " + related_spdx_element)


class TestLicense(TestCase):
    maxDiff = None

    def test_url(self):
        lic = License(full_name='Apache License 1.0', identifier='Apache-1.0')
        assert lic.url == 'http://spdx.org/licenses/Apache-1.0'

    def test_license_list(self):
        assert LICENSE_MAP['Aladdin Free Public License'] == 'Aladdin'
        assert LICENSE_MAP['Aladdin'] == 'Aladdin Free Public License'
        assert LICENSE_MAP['MIT License'] == 'MIT'
        assert LICENSE_MAP['MIT'] == 'MIT License'
        assert LICENSE_MAP['BSD 4-Clause "Original" or "Old" License'] == 'BSD-4-Clause'
        assert LICENSE_MAP['BSD-4-Clause'] == 'BSD 4-Clause "Original" or "Old" License'

    def test_from_full_name(self):
        mit = License.from_full_name('MIT License')
        assert mit.identifier == 'MIT'
        assert mit.url == 'http://spdx.org/licenses/MIT'

    def test_from_identifier(self):
        mit = License.from_identifier('MIT')
        assert mit.full_name == 'MIT License'
        assert mit.url == 'http://spdx.org/licenses/MIT'


class TestException(TestCase):

    def test_exception_list(self):
        assert EXCEPTION_MAP['Linux Syscall Note'] == 'Linux-syscall-note'
        assert EXCEPTION_MAP['Linux-syscall-note'] == 'Linux Syscall Note'
        assert EXCEPTION_MAP['GCC Runtime Library exception 3.1'] == 'GCC-exception-3.1'
        assert EXCEPTION_MAP['GCC-exception-3.1'] == 'GCC Runtime Library exception 3.1'
