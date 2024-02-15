"""A module implementing the worker."""

import os
import hou
import json
import datetime

# Fancy formatting
from rich.tree import Tree
from rich.theme import Theme
from rich.console import Console
from colorama import just_fix_windows_console


def terminal_report(report):
    """TBD"""
    # Initialize coloured output for windows
    just_fix_windows_console()

    # Specify themes, which will be used based on the check status
    theme = Theme({
        "pass": "green",
        "warn": "dark_orange",
        "fail": "bright_red",
        "error": "red1"
    })

    console = Console(theme=theme)

    asset_path = report["asset_path"]

    # Find the overall status
    overall_status = True
    for cur_report in report["reports"]:
        if cur_report["status"] != "pass":
            overall_status = False
            break

    status_emoji = ":white_check_mark:" if overall_status else ":x:"
    tree = Tree(f'{status_emoji} Checks for [bold]{asset_path}[/]')

    # Iterate over reports
    for cur_report in report["reports"]:
        cur_status = cur_report["status"]

        report_tree = tree.add(f'[b]{cur_report["node_name"]}[/]', style=cur_status)
        report_tree.add(f'[b][{cur_status}]{cur_status.upper()}[/][/] | [i]{cur_report["node_type"]}[/]', style="default")

        if cur_report["message"]:
            report_tree.add(cur_report["message"], style="default")

    print("\n")
    console.print(tree)


def parse_node_warnings(warnings):
    """TBD"""
    # Handle nodes without warnings, e.g. File SOP
    if not warnings:
        return {}

    # Assume a single warning per node
    # Strip 'Vex error: ' from the beginning of the warning, which VEX inserts
    warning_clean = warnings[0].lstrip("Vex error: ")
    warning_dict = json.loads(warning_clean)

    return warning_dict


def parse_node_errors(errors):
    """TBD"""
    return "\n".join(errors)


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
        cook_success = True
    except hou.OperationFailed:  # The cook has failed
        cook_success = False

    # The first report contains some metadata
    output = {
        "report_version": "1",
        "user": os.environ.get("USERNAME", ""),
        "node": os.environ.get("COMPUTERNAME", ""),
        "time": str(datetime.datetime.now()),
        "asset_path": chain[0].parm("file").eval(),
        "cook_success": cook_success,
        "reports": []
    }

    # Collect reports from the chain
    for chain_node in chain:
        if chain_node.type().name() in ["file"]:
            continue

        cur_warning = parse_node_warnings(chain_node.warnings())
        cur_error = parse_node_errors(chain_node.errors())

        # We assume that each check node has either an error or warning
        if cur_error:
            cur_status = "error"
        else:
            cur_status = cur_warning["status"]

        # Construct an individual report, add it to the list of reports
        output["reports"].append(
            {
                "node_name": chain_node.name(),
                "node_type": chain_node.type().name(),
                "status": cur_status,
                "message": cur_error if cur_error else cur_warning["message"]
            }
        )

    # Create reports folder if needed
    report_folder = os.path.dirname(json_path)
    os.makedirs(report_folder, exist_ok=True)

    # Save reports into a JSON file
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, sort_keys=True, indent=4)

    # Write results to standard output
    terminal_report(output)


def create_load_node(parent_node, asset_name, asset_path):
    """TBD"""
    node = parent_node.createNode("file", node_name=f"file_{asset_name}")
    node.parm("file").set(asset_path)

    return node


def create_check_nodes(parent_node, checks):
    """TBD"""
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
    """TBD"""
    # Houdini prefers forward slashes on all platforms
    report_path = os.path.join(os.path.dirname(asset_path),
                               "reports",
                               f"{asset_name}.json").replace("\\", "/")

    node = parent_node.createNode("dimension::report_json")
    node.parm("json_path").set(report_path)

    return node


def connect_node_chain(chain):
    """TBD"""
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
        hou.hipFile.save(args.scene, save_to_recent_files=False)

    # Create reports by triggering report nodes
    for report in report_nodes:
        report.parm("write").pressButton()
