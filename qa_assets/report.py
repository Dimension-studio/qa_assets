"""Implement the reporting functionality. This handles the passing of informatino out of Houdini nodes into a report saved on a disk."""

import os
import hou
import json
import datetime

# Fancy formatting
from rich.tree import Tree
from rich.theme import Theme
from rich.console import Console
from colorama import just_fix_windows_console

# Specify report version
REPORT_VERSION = "1.0"


def terminal_report(report):
    """Report checks results into the terminal with some nice formatting.

    Args:
        report (dict): A checks report

    Raises:
        AssertionError: When report's version does not match the expected one (specified in the `REPORT_VERSION` global var of this module)

    """
    # Make sure we are calling it with the expected report
    assert report["version"] == REPORT_VERSION, \
        f"""Report's version "{report["version"]}" does not match the expected one "{REPORT_VERSION}"""""

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


def get_input_nodes(node):
    """Construct a list of the input nodes from the specified `node`. It walks input connections until the end. The returned nodes will be in the "descending" order, but the last node (the passed `node`) is not included in the list. This includes only the first input.

    Args:
        node (hou.Node): Node which inputs will be collected

    Returns
        (:obj:`list` of :obj:`hou.Node`): All input nodes
    """
    chain = []

    cur_node = node
    while True:
        cur_parent = cur_node.inputs()

        if cur_parent:
            chain.insert(0, cur_parent[0])
            cur_node = cur_parent[0]
        else:
            break

    return chain


def get_output_nodes(node):
    """Construct a list of the output nodes from the specified `node`. It walks output connections until the end. The returned nodes will be in the "descending" order, but the first node (the passed `node`) is not included in the list. This includes only the first output.

    Args:
        node (hou.Node): Node which outputs will be collected

    Returns
        (:obj:`list` of :obj:`hou.Node`): All output nodes
    """
    chain = []

    cur_node = node
    while True:
        cur_child = cur_node.outputs()

        if cur_child:
            chain.append(cur_child[0])
            cur_node = cur_child[0]
        else:
            break

    return chain


def parse_node_warnings(warnings):
    """Parse the `warnings` string into a dictionary. The `warnings` is being accessed via Houdini's API and is set in VEX.

    Args:
        warnings (str): The string to be parsed

    Returns:
        dict: The parsed dict. The dict can be empty if a node does not report anything.

    """
    # Handle nodes without warnings, e.g. File SOP
    if not warnings:
        return {}

    # Assume a single warning per node
    # Strip 'Vex error: ' from the beginning of the warning, which VEX inserts
    warning_clean = warnings[0].lstrip("Vex error: ")
    warning_dict = json.loads(warning_clean)

    return warning_dict


def parse_node_errors(errors):
    """Parse the `errors` str list into a string. The `errors` is a list of error messages raised by a node in Houdini.

    Args:
        errors (:obj:`list` of :obj:`str`): The list to be parsed

    Returns:
        dict: The parsed str. The str can be empty if a node does not report anything.

    """
    return "\n".join(errors)


def write_json_report(report, json_path):
    """Write `report` into the specified `json_path`.

    Args:
        report (dict): The report to be saved
        json_path (str): File path where the report should be written into
    """
    # Create reports folder if needed
    report_folder = os.path.dirname(json_path)
    os.makedirs(report_folder, exist_ok=True)

    # Save reports into a JSON file
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, sort_keys=True, indent=4)


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

    # Build chain of parent (input) nodes, excluding the (last) Report JSON node
    chain = get_input_nodes(node)

    # Cook the report node
    try:
        node.cook()
        cook_success = True
    except hou.OperationFailed:  # The cook has failed
        cook_success = False

    # Populate the output dict with some metadata
    output = {
        "version": REPORT_VERSION,
        "user": os.environ.get("USERNAME", ""),
        "node": os.environ.get("COMPUTERNAME", ""),
        "time": str(datetime.datetime.now()),
        "asset_path": chain[0].parm("file").eval(),
        "cook_success": cook_success,
        "reports": []
    }

    # Collect reports from the chain
    for chain_node in chain:
        # Skip the "loader" nodes, e.g. a File SOP
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

    # Save JSON report
    write_json_report(output, json_path)

    # Write results to the terminal too
    terminal_report(output)
