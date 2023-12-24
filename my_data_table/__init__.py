import os
import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
_RELEASE = True

if not _RELEASE:
    _my_data_table = components.declare_component(
        "my_data_table",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _my_data_table = components.declare_component("my_data_table", path=build_dir)


def my_data_table(data, details=None, groupby=None, key=None):
    return _my_data_table(data=data, default=[], details=details, groupby=groupby, key=key)
