"""Perform unit tests."""

import hou
import json
import unittest

from qa_assets import report, check, run


class RunTests(unittest.TestCase):
    def test_verify_valid(self):
        pipe = """\
            {
                "nodes": [
                    {
                        "node_type_name": "file",
                        "parm_file": "$ASSET_INPUT_PATH"
                    },
                    {
                        "node_type_name": "clean",
                        "parm_fixoverlap": true
                    },
                                    {
                        "node_type_name": "report_json",
                        "parm_sopoutput": "$REPORT_PATH",
                        "press_write": true
                    },
                    {
                        "node_type_name": "rop_geometry",
                        "parm_sopoutput": "$ASSET_OUTPUT_PATH",
                        "press_execute": true
                    }
                ]
            }"""
        pipe_expected = json.loads(pipe)

        self.assertEqual(run.verify_pipeline(pipe), pipe_expected)

    def test_verify_1(self):
        pipe = """\
            {
                "foo": "bar"
            }"""

        with self.assertRaises(AssertionError):
            run.verify_pipeline(pipe)

    def test_verify_2(self):
        pipe = """\
            {
                "nodes": "bar"
            }"""

        with self.assertRaises(AssertionError):
            run.verify_pipeline(pipe)

    def test_verify_3(self):
        pipe = """\
            {
                "nodes": [1]
            }"""

        with self.assertRaises(AssertionError):
            run.verify_pipeline(pipe)

    def test_verify_4(self):
        pipe = """\
            {
                "nodes": [
                    {
                        "parm_file": "$ASSET_INPUT_PATH"
                    }
                ]
            }"""

        with self.assertRaises(AssertionError):
            run.verify_pipeline(pipe)

    def test_verify_5(self):
        pipe = """\
            {
                "nodes": [
                    {
                        "node_type_name": "file",
                        "foo": "bar"
                    }
                ]
            }"""

        with self.assertRaises(AssertionError):
            run.verify_pipeline(pipe)


class HoudiniTests(unittest.TestCase):
    def test_crete_connect_query_chain(self):
        # Prepare scene
        parent = hou.node("/obj").createNode("geo")

        check_names = [
            "check_normalized_uvs",
            "check_polycount",
            "asset_info",
            "clean",
            "facet"
        ]

        file_node = check.create_load_node(parent, "foo", "foo.obj")
        check_nodes = check.create_check_nodes(parent, check_names)
        report_node = check.create_report_node(parent, "foo", "foo.obj")

        chain = [file_node] + check_nodes + [report_node]
        check.connect_node_chain(chain)

        inputs = report.get_input_nodes(report_node)

        # Check things now
        # Check if nodes exist
        self.assertIsNotNone(parent.node("file_foo"))
        self.assertIsNotNone(parent.node("report_foo"))
        for name in check_names:
            self.assertIsNotNone(parent.node(f"{name}1"))

        # Check if the queried inputs are correct too
        expected_inputs = [
            parent.node("file_foo"),
            parent.node("check_normalized_uvs1"),
            parent.node("check_polycount1"),
            parent.node("asset_info1"),
            parent.node("clean1"),
            parent.node("facet1")
        ]
        self.assertEqual(inputs, expected_inputs)

    def tearDown(self):
        hou.hipFile.clear() # Clear up Houdini scene between tests


if __name__ == "__main__":
    unittest.main(verbosity=3)
