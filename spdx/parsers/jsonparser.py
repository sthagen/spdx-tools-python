# Copyright (c) Xavier Figueroa
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from spdx.parsers import jsonyamlxml


class Parser(jsonyamlxml.Parser):
    """
    Wrapper class for jsonyamlxml.Parser to provide an interface similar to
    RDF and TV Parser classes (i.e., spdx.parsers.<format name>.Parser) for JSON parser.
    It also avoids to repeat jsonyamlxml.Parser.parse code for JSON, YAML and XML parsers
    """

    def __init__(self, builder, logger):
        super(Parser, self).__init__(builder, logger)

    def parse(self, file):
        self.json_yaml_set_document(json.load(file))
        return super(Parser, self).parse()
