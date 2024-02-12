"""Build script."""

import os
import sys
import shutil
import subprocess


# https://github.com/AcademySoftwareFoundation/rez/wiki/Environment-Variables#build-environment-variables
PKG_NAME = os.environ["REZ_BUILD_PROJECT_NAME"]
PKG_VERSION = os.environ["REZ_BUILD_PROJECT_VERSION"]


def copytree_with_print(*args, **kwargs):
    """Wrap copytree, print out some debug info."""
    print(f"Copying directory from '{args[0]}' to '{args[1]}'")

    try:
        shutil.copytree(*args, **kwargs)
    except FileExistsError:
        # Rez creates the install_path automatically
        # This raises FileExistsError, so I remove it if it's empty
        # dirs_exist_ok=True is available since Python 3.8, but this is a workaround for earlier Python versions
        if "dst" in kwargs:
            install_path = kwargs["dst"]
        else:
            install_path = args[1]
        os.rmdir(install_path)

        shutil.copytree(*args, **kwargs)


def copy_with_print(*args, **kwargs):
    """Wrap copytree, print out some debug info."""
    print(f"Copying file from '{args[0]}' to '{args[1]}'")

    shutil.copy(*args, **kwargs)


def binarize_hdas(build_path):
    """Optimize HDAs."""
    # Binarize HDAs
    print("Starting HDA binarization")
    try:
        out = subprocess.check_output(["python", os.path.join(PKG_NAME, "__binarize.py"), os.path.join(build_path, PKG_NAME, "data", "otls", "*.hda")], stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise

    print(out)


def make_symlink(src_dir, dest_dir):
    """Make a directory symlink at `src_dir` pointing to `dest_dir`.

    This is a hacky workaround for Python < 3.8, which do not support symlinking (os.symlink) under unpriviledged user.
    """
    print(f"Symlinking directory '{src_dir}' to '{dest_dir}'")

    try:
        out = subprocess.check_output(["mklink", "/D", src_dir, dest_dir], stderr=subprocess.STDOUT, text=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise

    print(out)


def build_docs(build_path):
    """Build docs, so that they are included in the rez repo.

    `# pdoc -o docs -d google ./PKG_NAME`
    """
    print("Generating documentation")
    try:
        footer_text = f"{PKG_NAME}@{PKG_VERSION}"

        out = subprocess.check_output(["pdoc", "-o", os.path.join(build_path, "docs"), "-d", "google", "--footer-text", footer_text, f"./{PKG_NAME}"], stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise

    print(out)


def main(*, source_path, build_path, install_path, targets):
    """Build and install."""
    print("Starting build")
    copytree_with_print(
        os.path.join(source_path, PKG_NAME),
        os.path.join(build_path, PKG_NAME),
        ignore=shutil.ignore_patterns("*.pyc", "__pycache__", "*.~*~", "backup")
    )

    local_build = True if install_path.lower().startswith(os.environ["REZ_LOCAL_PACKAGES_PATH"].lower()) else False

    # Copy README.md, CHANGELOG.md
    copy_with_print(os.path.join(source_path, "README.md"), build_path)
    copy_with_print(os.path.join(source_path, "CHANGELOG.md"), build_path)

    # Skipping for now
    # if not local_build:
        # We don't use those (sources are symlinked), so can skip this step
        # binarize_hdas(build_path)

    build_docs(build_path)

    # "install" gets passed by rez, see the {install} placeholder in package.py
    if "install" in targets:
        if local_build:  # Local install - symlink instead of copy
            # Create a symlink in the local packages path pointing to the repository,
            # so that interactive work on files gets propagated back to the repo
            # breakpoint()
            print("Starting local installation (symlinking instead of copying).")

            copytree_with_print(build_path, install_path, ignore=shutil.ignore_patterns("*.pyc", "__pycache__", PKG_NAME))  # Note that we ignore PKG_NAME folder, which will get symlinked in the next step

            symlink_src = os.path.join(install_path, PKG_NAME)
            symlink_dest = os.path.join(os.path.dirname(os.environ["REZ_BUILD_SOURCE_PATH"]), PKG_NAME, PKG_NAME)

            make_symlink(symlink_src, symlink_dest)
        else:  # Probably a release install - copy files
            print("Starting release installation (copying instead of symlinking).")
            copytree_with_print(build_path, install_path, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))


if __name__ == "__main__":
    main(
        source_path=os.environ["REZ_BUILD_SOURCE_PATH"],  # Location where the package.py exists
        build_path=os.environ["REZ_BUILD_PATH"],
        install_path=os.environ["REZ_BUILD_INSTALL_PATH"],
        targets=sys.argv[1:]
    )
