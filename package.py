name = "qa_assets"

# Read version from version.py
@early()
def version():
    v_env = {}

    with open("qa_assets/version.py", encoding="utf-8") as fp:
        exec(fp.read(), v_env)

    return v_env["__version__"]

requires = [
    "houdini-19.0",
    "colorama",
    "rich"
]

build_requires = [
    "dev_env"
]

variants = [
    ["python-3.7"]
]

cachable = True

build_command = "python {root}/build.py {install}"


def commands():
    env.PATH.append("{root}/qa_assets/bin")

    # Python module
    env.PYTHONPATH.append("{root}")

    # Houdini config
    env.HOUDINI_PATH.prepend("{root}/qa_assets/data")
