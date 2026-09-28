# NetOps Automation Platform

A Python network automation platform that discovers network devices, collects
operational state, backs up configurations and checks live devices against a
declared source of truth.

The platform is developed and tested against a local network lab built with
Docker and FRRouting (FRR). The lab routers are Linux containers running FRR —
not physical or commercial network devices.

## Project Status

Work in progress — built incrementally as a hands-on NetOps portfolio project.

| Stage | Feature | Status |
|-------|---------|--------|
| 1 | Repository foundation | Done |
| 2 | Reproducible FRR eBGP lab | Done |
| 3 | Device discovery, BGP health, intent validation | Done |
| 4 | Configuration backup and change detection | Done |
| 5 | Configuration compliance engine | Done |

## Lab

Three FRR routers in an eBGP chain, defined in `lab/docker-compose.yml`.

```text
r1 (AS65001) ---- 10.0.12.0/29 ---- r2 (AS65002) ---- 10.0.23.0/29 ---- r3 (AS65003)
edge-router                         core-router                         edge-router
```

| Router | Container | Role | AS | Loopback | Management |
|--------|-----------|------|----|----------|------------|
| r1 | netops-r1 | edge-router | 65001 | 10.255.0.1/32 | 10.10.0.11 |
| r2 | netops-r2 | core-router | 65002 | 10.255.0.2/32 | 10.10.0.12 |
| r3 | netops-r3 | edge-router | 65003 | 10.255.0.3/32 | 10.10.0.13 |

- Each router advertises its loopback over eBGP.
- Router configurations live in `lab/frr/<router>/frr.conf` and are
  bind-mounted into the containers.
- The automation runs commands with `docker exec <container> vtysh -c "<command>"`
  and checks reachability with ICMP ping to the management IP.

## Architecture

```text
inventory/devices.yaml     source of truth: devices, ASN, expected BGP neighbors
        |
        v
inventory loader           validates the inventory, builds Device objects
        |
        v
connectors                 reachability (ICMP), command execution (docker exec vtysh)
        |
        v
collectors                 device info, BGP summary (JSON), running configuration
        |
        +--> discovery     BGP health, hostname/ASN validation
        +--> backup        SHA-256 fingerprint, latest/previous config, unified diff
        +--> compliance    rules -> engine -> report -> exit code
```

## Quick Start

Requirements: Linux, Docker with the Compose plugin, Python 3.12+.

```bash
git clone https://github.com/periclef/netops-automation-platform.git
cd netops-automation-platform

docker compose -f lab/docker-compose.yml up -d

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

BGP needs about a minute to converge after the lab starts.

## Usage

### Device discovery

```bash
python scripts/discover_devices.py
```

Collects hostname, FRR version, router ID, local AS and BGP peers for each
device, reports BGP health and validates hostname and ASN against the inventory.

```text
Discovery Summary
========================================================================
Devices:      3
Reachable:    3
Unreachable:  0
BGP Healthy:  3
Valid:        3
Invalid:      0
```

### Configuration backup

```bash
python scripts/backup_configs.py
```

Saves the running configuration of each router under `backups/<router>/` with a
SHA-256 fingerprint and metadata. Each run reports one of `INITIAL BACKUP`,
`NO CHANGE` or `CONFIGURATION CHANGED`; changes are shown as a unified diff
against the previous backup. `backups/` is runtime data and is not committed.

### Configuration compliance

```bash
python scripts/check_compliance.py
python scripts/check_compliance.py --device r1 --device r2
python scripts/check_compliance.py --inventory path/to/devices.yaml
```

Compares the live state of each router with the intent declared in the
inventory:

| Rule | Checks | Type |
|------|--------|------|
| Hostname | hostname matches the inventory | configuration |
| Local ASN | local BGP AS matches the inventory | configuration |
| BGP Peer | each declared neighbor exists with the expected remote AS | configuration |
| BGP Session | each declared neighbor is `Established` | operational |
| Unexpected BGP Peers | no neighbors exist that are not declared in the inventory | drift |

Example (real output from the lab):

```text
Device: r1

[PASS] Hostname
       expected=r1
       actual=r1

[PASS] Local ASN
       expected=65001
       actual=65001

[PASS] BGP Peer
       expected=10.0.12.3 AS65002
       actual=10.0.12.3 AS65002

[PASS] BGP Session
       expected=10.0.12.3 Established
       actual=10.0.12.3 Established

[PASS] Unexpected BGP Peers
       expected=<none>
       actual=<none>

Compliance: PASS
```

| Exit code | Meaning |
|-----------|---------|
| 0 | all devices compliant |
| 1 | at least one violation (including unreachable devices) |
| 2 | tool error (invalid inventory, unknown device) |

Unreachable devices and state collection failures are reported as `FAIL` —
a device is never considered compliant without evidence.

Failure scenarios executed against the lab (wrong remote AS, unauthorized
neighbor, hostname drift, router stopped, frozen control plane) are documented
in [docs/failure-scenarios.md](docs/failure-scenarios.md).

## Testing and CI

```bash
ruff check .
pytest -v
```

- Unit tests cover the inventory loader, collectors, backup, diff, validation
  and all compliance rules. They use simulated device state and do not require
  the lab.
- GitHub Actions (`.github/workflows/ci.yml`) runs ruff and pytest on every
  pull request and push to `main`, on Python 3.12 (minimum supported) and 3.14.
  The workflow token is read-only.
- The FRR lab is not started in CI. Behaviour against live routers is tested
  manually and documented in `docs/failure-scenarios.md`.

## Repository Structure

```text
.
├── .github/workflows/ci.yml   # lint and tests
├── docs/
│   ├── architecture.md
│   └── failure-scenarios.md
├── inventory/devices.yaml     # source of truth
├── lab/
│   ├── docker-compose.yml     # three FRR routers
│   └── frr/r1..r3/            # daemons, frr.conf, vtysh.conf
├── scripts/
│   ├── backup_configs.py
│   ├── check_compliance.py
│   └── discover_devices.py
├── src/netops/
│   ├── backup/                # backup manager, configuration diff
│   ├── collectors/            # device info, BGP summary, configuration
│   ├── compliance/            # rules, engine, report
│   ├── connectors/            # reachability, FRR docker exec
│   ├── inventory/             # inventory loader and validation
│   ├── models/                # Device, BgpNeighbor
│   ├── utils/
│   └── validators/            # hostname/ASN validation used by discovery
└── tests/                     # pytest unit tests
```

## Security

- The lab needs no credentials: routers are accessed with `docker exec`.
- `.env.example` contains placeholders for future SSH-based connectors; these
  variables are not used by the current code. A real `.env` must never be
  committed.
- All IP addresses and AS numbers are private lab values.
- Configuration backups (`backups/`) are excluded from Git.

## Limitations

- Only FRR in Docker is supported; SSH, NETCONF or API-based connectors for
  real network devices are not implemented yet.
- The compliance engine is a point-in-time check. Detection of silent failures
  is bounded by BGP timers.
- Hostname drift cannot be reproduced in the lab: FRR daemons inherit the
  container hostname.

## License

MIT — see [LICENSE](LICENSE).
