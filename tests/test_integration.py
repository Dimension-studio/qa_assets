"""Perform integration tests."""

import os
import shutil
import unittest
import subprocess


class TestRun(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.outputs = ["1.obj", "2.bgeo.sc", "3.bgeo.sc", "4.fbx", "missing"]

    def setUp(self):
        #Remove previous reports, outputs
        shutil.rmtree("tests\\tmp\\test_geo_run\\reports", ignore_errors=True)
        shutil.rmtree("tests\\tmp\\test_geo_run\\otuputs", ignore_errors=True)

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
                        "node_type_name": "check_polycount"
                    },
                    {
                        "node_type_name": "check_normalized_uvs"
                    },
                    {
                        "node_type_name": "asset_info"
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
            }""".replace(" ", "").replace("\n", "")

        cmd = [
            "qa.cmd", "run",
            "--pipeline", pipe
        ]

        for output in self.outputs:
            cmd.extend(["--asset",
                        os.path.join("tests\\tmp\\test_geo_run", output)
            ])

        cmd.extend([
            "--scene",
            "tests\\tmp\\run.hip"
        ])

        # Run QA checks
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # stdout=subprocess.DEVNULL


    def test_schema(self):
        cmd = [
            "rez", "env", "check_jsonschema", "--",
            "check-jsonschema", "--verbose",
            "--schemafile", "qa_assets\\data\\schemas\\report_v1.0.schema.json"
        ]

        for output in self.outputs:
            cmd.append(os.path.join("tests\\tmp\\test_geo_run\\reports", 
                                    output + ".json"))

        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)


class TestCheck(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.outputs = ["1.obj", "2.bgeo.sc", "3.bgeo.sc", "4.fbx", "missing"]

    def setUp(self):
        #Remove previous reports
        shutil.rmtree("tests\\tmp\\test_geo\\reports", ignore_errors=True)

        cmd = [
            "qa.cmd", "check",
            "--check", "check_normalized_uvs",
            "--check", "check_polycount",
            "--check", "asset_info"
        ]

        for output in self.outputs:
            cmd.extend(["--asset",
                        os.path.join("tests\\tmp\\test_geo", output)
            ])

        cmd.extend([
            "--scene",
            "tests\\tmp\\check.hip"
        ])

        # Run QA checks
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)  # stdout=subprocess.DEVNULL


    def test_schema(self):
        cmd = [
            "rez", "env", "check_jsonschema", "--",
            "check-jsonschema", "--verbose",
            "--schemafile", "qa_assets\\data\\schemas\\report_v1.0.schema.json"
        ]

        for output in self.outputs:
            cmd.append(os.path.join("tests\\tmp\\test_geo\\reports", 
                                    output + ".json"))

        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main(verbosity=3)