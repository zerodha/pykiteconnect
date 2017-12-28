# coding: utf-8
def assert_dict_keys(inp, keys):
    """Check if all keys given as a list is there in input"""
    for k in keys:
        assert k in inp
