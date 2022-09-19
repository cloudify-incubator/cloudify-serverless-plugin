import os

import mock
import tempfile
import unittest

from cloudify.exceptions import NonRecoverableError

from .. import utils


class ServerlessUtilsTestBase(unittest.TestCase):

    def test_generate_traceback_exception(self):
        try:
            raise Exception('foo bar')
        except Exception:
            exception = utils.generate_traceback_exception()
            self.assertIn('foo bar', str(exception))

    def test_find_rels_by_node_type(self):
        mock_node1 = mock.Mock(type_hierarchy='qux')
        mock_target1 = mock.Mock(node=mock_node1)
        mock_rel1 = mock.Mock(target=mock_target1)
        mock_node2 = mock.Mock(type_hierarchy='quux')
        mock_target2 = mock.Mock(node=mock_node2)
        mock_rel2 = mock.Mock(target=mock_target2)
        node_instance = mock.Mock(relationships=[mock_rel1, mock_rel2])
        rels = utils.find_rels_by_node_type(node_instance, 'quux')
        self.assertIn(
            mock_rel2,
            rels
        )
        self.assertNotIn(
            mock_rel1,
            rels
        )

    def test_validate_executable_file(self):
        with tempfile.NamedTemporaryFile() as test_file:
            self.assertRaisesRegex(
                NonRecoverableError,
                r'the file is not executable',
                utils.validate_executable_file,
                test_file.name
            )
        self.assertRaisesRegex(
            NonRecoverableError,
            r'the file does not exist',
            utils.validate_executable_file,
            '/foo/bar'
        )
        self.assertFalse(utils.validate_executable_file(''))

    def test_verify_executable(self):
        mock_node1 = mock.Mock(type_hierarchy='qux')
        mock_target1 = mock.Mock(node=mock_node1)
        mock_rel1 = mock.Mock(target=mock_target1)
        mock_node2 = mock.Mock(type_hierarchy=utils.BINARY_TYPE)
        mock_instance2 = mock.Mock(runtime_properties={})
        mock_target2 = mock.Mock(
            node=mock_node2, instance=mock_instance2)
        mock_rel2 = mock.Mock(target=mock_target2)
        node_instance = mock.Mock(
            relationships=[mock_rel1, mock_rel2],
            runtime_properties={},
        )
        self.assertRaisesRegexp(
            NonRecoverableError,
            r'Failed to locate valid serverless executable.',
            utils.verify_executable,
            config={},
            node_instance=node_instance
        )
        with tempfile.NamedTemporaryFile() as test_file:
            os.chmod(test_file.name, 0o0770)
            mock_node3 = mock.Mock(type_hierarchy=utils.BINARY_TYPE)
            mock_instance3 = mock.Mock(
                runtime_properties={
                    'executable_path': test_file.name,
                }
            )
            mock_target3 = mock.Mock(
                node=mock_node3, instance=mock_instance3)
            mock_rel3 = mock.Mock(target=mock_target3)
            node_instance3 = mock.Mock(
                relationships=[mock_rel3],
                runtime_properties={},
            )
            self.assertEqual(
                utils.verify_executable({}, node_instance3),
                {
                    'executable_path': test_file.name
                }
            )
        with tempfile.NamedTemporaryFile() as test_file:
            os.chmod(test_file.name, 0o0770)
            node_instance4 = mock.Mock(
                runtime_properties={
                    'executable_path': test_file.name
                },
            )
            self.assertEqual(
                utils.verify_executable({}, node_instance4),
                {
                    'executable_path': test_file.name
                }
            )
