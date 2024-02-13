"""A module implementing the worker."""

import os
import hou


def parse_node_warnings(warnings):
    """TBD"""
    return warnings


def parse_node_errors(errors):
    """TBD"""
    return errors


def report_json_callback(kwargs):
    """Collect node reports and write them to a json file.

    Args:
        kwargs (dict): Houdini-passed dict containing some context, e.g.:
            `{
                'node': <hou.SopNode of type dimension::report_json::0.0.1 at /obj/checks/report_json1>,
                'parm': <hou.Parm write in /obj/checks/report_json1>,
                'script_multiparm_index': '-1',
                'script_value0': '0',
                'script_value': '0',
                'parm_name': 'write',
                'script_multiparm_nesting': '0',
                'script_parm': 'write'
            }`
            See https://www.sidefx.com/docs/houdini/hom/locations#parameter_callback_scripts for more
    """
    node = kwargs["node"]
    json_path = node.parm("json_path").eval()

    # Build chain of parent (input) nodes, excluding the Report JSON node
    chain = []
    cur_node = node
    while True:
        cur_parent = cur_node.inputs()

        if cur_parent:
            chain.insert(0, cur_parent[0])
            cur_node = cur_parent[0]
        else:
            break

    # Cook the report node
    try:
        node.cook()
        cooked = True
    except hou.OperationFailed:  # The cook has failed
        cooked = False

    # Collect reports from the chain
    for chain_node in chain:
        if cooked:
            cur_status = parse_node_warnings(chain_node.warnings())
        else:
            cur_status = parse_node_errors(chain_node.errors())

        print(cur_status)

    print()


def check(args):
    """Check subcommand.

    Args:
        args (argparse.ArgumentParser): Parsed arguments

    Raises:
        ValueError: If a check node could not be created, e.g. if a such node does not exist
    """
    checks_geo = hou.node("/obj").createNode("geo", node_name="checks")

    # Store Report JSON nodes here, so that they can be triggerred later
    report_nodes = []

    # Iterate over assets
    for asset in args.asset:
        asset_path_abs = os.path.abspath(asset)
        asset_path = asset
        asset_name = os.path.basename(asset_path)

        # Load asset
        file = checks_geo.createNode("file", node_name=f"file_{asset_name}")
        file.parm("file").set(asset_path)

        # Iterate over checks, create the node chain (file -> check1 -> check2 -> ...)
        chain = [file]

        # Create nodes
        for check_name in args.check:
            try:
                check_node = checks_geo.createNode(check_name)
            except hou.OperationFailed as e:
                # Reraise invalid node type name as ValueError
                if e.instanceMessage() == "Invalid node type name":
                    raise ValueError(f"Invalid node name: '{check_name}'") from e

                raise

            chain.append(check_node)

        # Create the Report JSON node
        report_path = os.path.join(os.path.dirname(asset_path_abs),
                                   "reports",
                                   f"{asset_name}.json").replace("\\", "/")  # Houdini prefers forward slashes on all platforms

        report_node = checks_geo.createNode("dimension::report_json")
        report_node.parm("json_path").set(report_path)

        chain.append(report_node)
        report_nodes.append(report_node)

        # Create node connections
        for i, node in enumerate(chain):
            if i == 0:  # Skip the 1st node
                continue

            node.setFirstInput(chain[i - 1])

    # Layout
    checks_geo.layoutChildren()

    # Save scene for debugging
    if args.scene:
        hou.hipFile.save(args.scene, save_to_recent_files=False)

    # Create reports by triggering report nodes
    for report in report_nodes:
        report.parm("write").pressButton()
