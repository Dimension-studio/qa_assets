"""Perform integration tests."""

import os
import shutil
import unittest
import subprocess


class TestJsonSchema(unittest.TestCase):
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
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)


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