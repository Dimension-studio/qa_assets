"""Perform unit tests."""

import hou
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
                        "parm_json_path": "$REPORT_PATH",
                        "press_write": true
                    },
                    {
                        "node_type_name": "rop_geometry",
                        "parm_sopoutput": "$ASSET_OUTPUT_PATH",
                        "press_execute": true
                    }
                ]
            }"""

        pipe_expected = {
           "nodes": [
                {
                    "node_type_name": "file",
                    "parm_file": "$ASSET_INPUT_PATH"
                },
                {
                    "node_type_name": "clean",
                    "parm_fixoverlap": True
                },
                                {
                    "node_type_name": "report_json",
                    "parm_json_path": "$REPORT_PATH",
                    "press_write": True
                },
                {
                    "node_type_name": "rop_geometry",
                    "parm_sopoutput": "$ASSET_OUTPUT_PATH",
                    "press_execute": True
                }
            ]
        }

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

    def test_substitutions(self):
        asset = "path\\to\\assets\\foo.fbx"

        subs = run.generate_substitutions(asset)
        expected_subs = {
            "$ASSET_INPUT_PATH": "path/to/assets/foo.fbx",
            "$REPORT_PATH": "path/to/assets/reports/foo.fbx.json",
            "$ASSET_OUTPUT_PATH": "path/to/assets/outputs/foo.fbx"
        }

        self.assertEqual(subs, expected_subs)


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

    def test_nodes_from_pipe(self):
        parent = hou.node("/obj").createNode("geo")

        asset = "path\\to\\assets\\foo.fbx"
        subs = run.generate_substitutions(asset)

        pipe = {
           "nodes": [
                {
                    "node_type_name": "file",
                    "parm_file": "$ASSET_INPUT_PATH"
                },
                {
                    "node_type_name": "clean",
                    "parm_fixoverlap": True
                },
                {
                    "node_type_name": "report_json",
                    "parm_json_path": "$REPORT_PATH",
                    "press_write": True
                },
                {
                    "node_type_name": "rop_geometry",
                    "parm_sopoutput": "$ASSET_OUTPUT_PATH",
                    "press_execute": True
                }
            ]
        }

        nodes, buttons = run.create_nodes_from_pipeline(pipe, parent, subs)

        # Checks
        # Check if nodes got created
        check_names = [
            "file1",
            "clean1",
            "report_json1",
            "rop_geometry1",
        ]
        for name in check_names:
            self.assertIsNotNone(parent.node(name))

        # Check buttons
        self.assertEqual(len(buttons), 2)
        self.assertEqual(buttons[0].name(), "write")
        self.assertEqual(buttons[1].name(), "execute")

        # Check parm values
        self.assertEqual(
            parent.node("file1").parm("file").eval(),
            subs["$ASSET_INPUT_PATH"]
        )

        self.assertEqual(
            parent.node("clean1").parm("fixoverlap").eval(),
            1
        )

        self.assertEqual(
            parent.node("report_json1").parm("json_path").eval(),
            subs["$REPORT_PATH"]
        )

        self.assertEqual(
            parent.node("rop_geometry1").parm("sopoutput").eval(),
            subs["$ASSET_OUTPUT_PATH"]
        )

    def test_nodes_from_pipe_bad_node(self):
        parent = hou.node("/obj").createNode("geo")

        asset = "path\\to\\assets\\foo.fbx"
        subs = run.generate_substitutions(asset)

        pipe = {
            "nodes": [
                {
                    "node_type_name": "asdgfdgfdasfsdsf",
                }
            ]
        }

        with self.assertRaises(ValueError):
            run.create_nodes_from_pipeline(pipe, parent, subs)

    def test_nodes_from_pipe_bad_parm(self):
        parent = hou.node("/obj").createNode("geo")

        asset = "path\\to\\assets\\foo.fbx"
        subs = run.generate_substitutions(asset)

        pipe = {
            "nodes": [
                {
                    "node_type_name": "file",
                    "parm_dasddsadapoda": "foobar"
                }
            ]
        }

        with self.assertRaises(ValueError):
            run.create_nodes_from_pipeline(pipe, parent, subs)

    def test_input_nodes(self):
        parent = hou.node("/obj").createNode("geo")

        file = parent.createNode("file")
        clean = parent.createNode("clean")
        facet = parent.createNode("facet")

        check.connect_node_chain([file, clean, facet])

        self.assertEqual(
            report.get_input_nodes(facet),
            [file, clean]
        )

    def test_input_nodes_empty(self):
        parent = hou.node("/obj").createNode("geo")

        file = parent.createNode("file")

        self.assertEqual(
            report.get_input_nodes(file),
            []
        )

    def test_output_nodes(self):
        parent = hou.node("/obj").createNode("geo")

        file = parent.createNode("file")
        clean = parent.createNode("clean")
        facet = parent.createNode("facet")

        check.connect_node_chain([file, clean, facet])

        self.assertEqual(
            report.get_output_nodes(file),
            [clean, facet]
        )

    def test_output_nodes_empty(self):
        parent = hou.node("/obj").createNode("geo")

        file = parent.createNode("file")

        self.assertEqual(
            report.get_output_nodes(file),
            []
        )

    def test_input_output_nodes_chain(self):
        parent = hou.node("/obj").createNode("geo")

        file = parent.createNode("file")
        clean = parent.createNode("clean")
        facet = parent.createNode("facet")

        check.connect_node_chain([file, clean, facet])

        self.assertEqual(
            report.get_input_nodes(clean) + [clean] + report.get_output_nodes(clean),
            [file, clean, facet]
        )

    def tearDown(self):
        hou.hipFile.clear() # Clear up Houdini scene between tests


if __name__ == "__main__":
    unittest.main(verbosity=3)
