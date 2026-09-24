from netops.backup.diff import generate_config_diff


def test_detects_removed_configuration_line():
    previous = """interface lo
 ip address 10.255.0.2/32
 ip address 10.255.100.2/32
exit
"""

    current = """interface lo
 ip address 10.255.0.2/32
exit
"""

    diff = generate_config_diff(
        previous,
        current,
    )

    assert "- ip address 10.255.100.2/32" in diff


def test_detects_added_configuration_line():
    previous = """interface lo
 ip address 10.255.0.2/32
exit
"""

    current = """interface lo
 ip address 10.255.0.2/32
 ip address 10.255.100.2/32
exit
"""

    diff = generate_config_diff(
        previous,
        current,
    )

    assert "+ ip address 10.255.100.2/32" in diff


def test_identical_configs_have_no_diff():
    config = """interface lo
 ip address 10.255.0.2/32
exit
"""

    diff = generate_config_diff(
        config,
        config,
    )

    assert diff == ""
