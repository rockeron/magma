"""
Copyright (c) 2018-present, Facebook, Inc.
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree. An additional grant
of patent rights can be found in the PATENTS file in the same directory.
"""

import unittest
from unittest import mock

from google.protobuf import any_pb2
from google.protobuf.json_format import MessageToJson
from magma.configuration import mconfig_managers
from orc8r.protos import mconfig_pb2
from orc8r.protos.mconfig import mconfigs_pb2


class StreamedMconfigManagerTest(unittest.TestCase):
    @mock.patch('magma.configuration.service_configs.get_service_config_value')
    def test_load_mconfig(self, get_service_config_value_mock):
        # Fixture mconfig has 1 missing service, 1 unregistered type
        magmad_fixture = mconfigs_pb2.MagmaD(
            checkin_interval=10,
            checkin_timeout=5,
            autoupgrade_enabled=True,
            autoupgrade_poll_interval=300,
            package_version='1.0.0-0',
            images=[],
            tier_id='default',
            feature_flags={'flag1': False},
        )
        magmad_fixture_any = any_pb2.Any()
        magmad_fixture_any.Pack(magmad_fixture)
        magmad_fixture_serialized = MessageToJson(magmad_fixture_any)
        fixture = '''
        {
            "offset": 42,
            "configs": {
                "configs_by_key": {
                    "magmad": %s,
                    "mme": {
                        "@type": "type.googleapis.com/magma.mconfig.NotAType",
                        "value": "test1"
                    },
                    "not_a_service": {
                        "@type": "type.googleapis.com/magma.mconfig.MagmaD",
                        "value": "test2"
                    }
                }
            }
        }
        ''' % magmad_fixture_serialized
        get_service_config_value_mock.return_value = ['mme']

        with mock.patch('builtins.open', mock.mock_open(read_data=fixture)):
            manager = mconfig_managers.StreamedMconfigManager()
            actual = manager.load_mconfig()
            expected_configs_by_key = {'magmad': magmad_fixture_any}
            expected = mconfig_pb2.OffsetGatewayConfigs(
                offset=42,
                configs=mconfig_pb2.GatewayConfigs(
                    configs_by_key=expected_configs_by_key,
                ),
            )
            self.assertEqual(expected, actual)