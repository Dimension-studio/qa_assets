"""A module implementing the worker."""

import os
import hou
import json

from .check import connect_node_chain


def verify_pipeline(pipeline):
    """Verify the passed `pipeline` string. This performs a series of checks to make sure that the passd `pipeline` has the expected structure.

    Args:
        pipeline (str): The pipeline to be checked

    Raises:
        AssertionError: When one of the checks has failed

    Returns:
        dict: If all the checks have passed then it returns a `dict` of the `pipeline` JSON string

    """
    pipe_dict = json.loads(pipeline)
    msg_prefix = "PIPELINE VERIFICATION: "

    assert list(pipe_dict.keys()) == ["nodes"], msg_prefix + "The passed pipeline is missing the 'nodes' key in its root"

    assert isinstance(pipe_dict["nodes"], list), msg_prefix + "The passed pipeline does not have a list under the 'nodes' key."

    for node in pipe_dict["nodes"]:
        assert isinstance(node, dict), msg_prefix + "Node is not a dict"

        assert node.get("node_type_name") is not None, msg_prefix + "Node is missing 'node_type_name' key"

        for key in node:
            if key == "node_type_name":
                continue
            if key.startswith("parm_"):
                continue
            if key.startswith("press_"):
                continue
            assert False, msg_prefix + "Unexpected key in the node"

    return pipe_dict


def create_nodes_from_pipeline(pipeline, parent_node, subsitutions):
    """TBD"""
    # Handle incorrect node name
    # Handle incorrect parm / button name
    pipeline_nodes = pipeline["nodes"]

    nodes = []
    buttons = []

    # Create nodes
    for node_dict in pipeline_nodes:
        cur_node_name = node_dict["node_type_name"]

        # Try instantiating the Houdini node
        try:
            cur_node = parent_node.createNode(cur_node_name)
        except hou.OperationFailed as e:
            # Reraise invalid node type name as ValueError
            if e.instanceMessage() == "Invalid node type name":
                raise ValueError(f"Invalid node name: '{cur_node_name}'") from e

            raise  # Reraise the original exception - in case something else has happened

        # Set node's parms from the node_dict
        # Store buttons to be pressed
        for key, value in node_dict.items():
            if key.startswith("parm_"):
                cur_parm_name = key.replace("parm_", "")
                cur_parm = cur_node.parm(cur_parm_name)

                # Check if the parm name is correct
                if cur_parm is None:
                    raise ValueError(f"Invalid parm name: '{cur_parm_name}' in '{cur_node_name}'")

                # Handle special cases - variables that need to be substituted
                substituted = False
                for sub_key, sub_value in subsitutions.items():
                    if value == sub_key:
                        cur_parm.set(sub_value)
                        substituted = True

                # Finally set parm's value if a substitiuon hasn't happenned
                if not substituted:
                    cur_parm.set(value)

            elif key.startswith("press_"):
                cur_button_name = key.replace("press_", "")
                cur_button = cur_node.parm(cur_button_name)

                # Check if the parm name is correct
                if cur_button is None:
                    raise ValueError(f"Invalid button name: '{cur_button_name}' in '{cur_node_name}'")

                buttons.append(cur_button)

        nodes.append(cur_node)

    return nodes, buttons


def generate_substitutions(asset_path):
    """TBD"""
    asset_name = os.path.basename(asset_path)

    # Houdini prefers forward slashes on all platforms
    asset_input_path = asset_path.replace("\\", "/")

    report_path = os.path.join(os.path.dirname(asset_path),
                               "reports",
                               f"{asset_name}.json").replace("\\", "/")

    asset_output_path = os.path.join(os.path.dirname(asset_path),
                                     "outputs",
                                     f"{asset_name}").replace("\\", "/")

    substitutions = {
        "$ASSET_INPUT_PATH": asset_input_path,
        "$REPORT_PATH": report_path,
        "$ASSET_OUTPUT_PATH": asset_output_path
    }

    return substitutions


def run(args):
    """Run subcommand.

    An example pipeline can look like this:
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
        }

    Args:
        args (argparse.ArgumentParser): Parsed arguments

    Raises:
        ValueError: If a check node could not be created, e.g. if a such node does not exist
    """
    # Read the pipeline from argument, or file
    if args.pipeline:
        pipe_str = args.pipeline
    elif args.pipeline_file:
        with open(args.pipeline_file, encoding="utf-8") as f:
            pipe_str = f.read()

    pipe = verify_pipeline(pipe_str)

    checks_geo = hou.node("/obj").createNode("geo", node_name="checks")

    buttons_to_be_pressed = []

    # Iterate over assets
    for asset_path in args.asset:
        # Specify substitutions
        substitutions = generate_substitutions(asset_path)

        # Create nodes from pipeline
        cur_nodes, cur_buttons = create_nodes_from_pipeline(pipe, checks_geo, substitutions)

        # Connect our nodes
        connect_node_chain(cur_nodes)

        buttons_to_be_pressed.extend(cur_buttons)

    # Press buttons
    for button in buttons_to_be_pressed:
        button.pressButton()

    # Layout
    checks_geo.layoutChildren()

    # Save scene for debugging
    if args.scene:
        hou.hipFile.save(args.scene.replace("\\", "/"),
                         save_to_recent_files=False)
