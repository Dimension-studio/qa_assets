"""A module implementing the worker."""

import os
import hou


def check(args):
    """Check subcommand.

    Args:
        args (argparse.ArgumentParser): Parsed arguments

    Raises:
        ValueError: If a check node could not be created, e.g. if a such node does not exist
    """
    checks_geo = hou.node("/obj").createNode("geo", node_name="checks")

    # Iterate over assets
    for asset in args.asset:
        asset_path = os.path.normpath(asset)
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
