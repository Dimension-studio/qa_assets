"""Repository for the automated assets quality assurance."""

import sys
import argparse


def check(args):
    """Check subcommand."""
    print(args.check)
    print(args.asset)


def submit(args):
    """Submit subcommand."""
    print("submit called")
    raise NotImplementedError("Submit not yet implemented.")


def parse_args(args):
    """Parse arguments and creates help information.

    Args:
        args: List of system arguments, excluding the first one - path of the script

    Returns:
        argparse.ArgumentParser: Parser object that can be used to retreive arguments

    """
    # Parser, subcommand setup
    parser = argparse.ArgumentParser(description="Automated assets quality assurance",
                                     prog="qa")
    subparsers = parser.add_subparsers(title="subcommand",
                                       required=True,
                                       description="Choose the desired action",
                                       dest="subcommand")

    parser_check = subparsers.add_parser("check", help="The worker")
    parser_check.set_defaults(func=check)

    parser_submit = subparsers.add_parser("submit", help="The submitter")
    parser_submit.set_defaults(func=submit)

    # Check args
    parser_check.add_argument("--check",
                              help="Specify the check that should be executed, multiple checks are allowed.",
                              required=True,
                              action="append")
    parser_check.add_argument("--asset",
                              help="Specify the asset that the check(s) should be applied to, multiple assets are allowed.",
                              required=True,
                              action="append")

    # Submit args
    parser_submit.add_argument("--check",
                               help="Specify the check that should be executed, multiple checks are allowed.",
                               required=True,
                               action="append")
    parser_submit.add_argument("--asset",
                               help="Specify the asset that the check(s) should be applied to, multiple assets are allowed.",
                               action="append")
    parser_submit.add_argument("--assets_pattern",
                               help="Specify the glob pattern for assets that the check(s) should be applied to, multiple assets patterns are allowed.",
                               action="append")

    return parser.parse_args(args)


def main():
    """Parse arguments and call the corresponding subcommand function."""
    args = parse_args(sys.argv[1:])

    # Call the subcommand function
    args.func(args)


if __name__ == "__main__":
    main()
