"""A module implementing the worker."""

import os
import hou


def create_load_node(parent_node, asset_name, asset_path):
    """Create a geometry load node in the specified `parent_node` loading `asset_path`.

    Args:
        parent_node (hou.Node): Parent node in which the loader node will be created
        asset_name (str): Name of the asset, will be used for naming the loader node
        asset_path (str): File path of the asset that should be loaded in Houdini

    Returns:
        hou.Node: The newly created loader node

    """
    node = parent_node.createNode("file", node_name=f"file_{asset_name}")
    node.parm("file").set(asset_path.replace("\\", "/"))  # Use forward slashes

    return node


def create_check_nodes(parent_node, checks):
    """Iterate over node names in `checks` and create them.

    Args:
        parent_node (hou.Node): Parent node in which the checks nodes will be created in
        checks (:obj:`list` of :obj:`str`): Names of Houdini nodes that should be created

    Raises:
        ValueError: When an invalid node name was passed

    Returns:
        (:obj:`list` of :obj:`hou.Node`): Created nodes, in the same order as specified in `checks`

    """
    chain = []

    for check_name in checks:
        try:
            check_node = parent_node.createNode(check_name)
        except hou.OperationFailed as e:
            # Reraise invalid node type name as ValueError
            if e.instanceMessage() == "Invalid node type name":
                raise ValueError(f"Invalid node name: '{check_name}'") from e

            raise  # Reraise the original exception - in case something else has happened

        chain.append(check_node)

    return chain


def create_report_node(parent_node, asset_name, asset_path):
    """Create a report node which will handle passing information out of Houdini.

    Args:
        parent_node (hou.Node): Parent node in which the report node will be created
        asset_name (str): Name of the asset, will be used for naming the report node
        asset_path (str): File path of the asset that is being processed

    Returns:
        hou.Node: The newly created report node

    """
    # Maybe this (specifying the report path) should be split into a designated function
    # Houdini prefers forward slashes on all platforms
    report_path = os.path.join(os.path.dirname(asset_path),
                               "reports",
                               f"{asset_name}.json").replace("\\", "/")

    node = parent_node.createNode("dimension::report_json")
    node.parm("json_path").set(report_path)

    return node


def connect_node_chain(chain):
    """Connect Houdini nodes in `chain` together. This connects one node's first output to the next node's first input.

    Args:
        chain (:obj:`list` of :obj:`hou.Node`): Nodes to be connected together
    """
    for i, node in enumerate(chain):
        if i == 0:  # Skip the 1st node
            continue

        node.setFirstInput(chain[i - 1])


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
        file = create_load_node(checks_geo, asset_name, asset_path)

        # Create check nodes
        check_nodes = create_check_nodes(checks_geo, args.check)

        # Create the Report JSON node
        report_node = create_report_node(checks_geo, asset_name, asset_path_abs)

        # Create a node chain for the current asset (file -> check1 -> check2 -> ... -> report)
        chain = [file] + check_nodes + [report_node]

        # Create node connections
        connect_node_chain(chain)

        report_nodes.append(report_node)

    # Layout
    checks_geo.layoutChildren()

    # Save scene for debugging
    if args.scene:
        hou.hipFile.save(args.scene.replace("\\", "/"),
                         save_to_recent_files=False)

    # Create reports by triggering report nodes
    for report in report_nodes:
        report.parm("write").pressButton()
