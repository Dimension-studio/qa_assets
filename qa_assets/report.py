"""TBD"""

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


def get_input_nodes(node):
    """TBD"""
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


def write_json_report(report, json_path):
    """TBD"""
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

    # Populate output dict with some metadata
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
