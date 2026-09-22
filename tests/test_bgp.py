from netops.collectors.bgp import is_bgp_healthy


def test_bgp_healthy_when_all_peers_established():
    summary = {
        "total_peers": 2,
        "established_peers": 2,
    }

    assert is_bgp_healthy(summary) is True


def test_bgp_unhealthy_when_peer_is_down():
    summary = {
        "total_peers": 2,
        "established_peers": 1,
    }

    assert is_bgp_healthy(summary) is False


def test_bgp_unhealthy_when_no_peers_exist():
    summary = {
        "total_peers": 0,
        "established_peers": 0,
    }

    assert is_bgp_healthy(summary) is False
