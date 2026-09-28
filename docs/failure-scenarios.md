# Failure Scenarios — Configuration Compliance Engine

All scenarios below were executed against the FRR/Docker lab
(r1 AS65001 — r2 AS65002 — r3 AS65003, eBGP chain) using
`scripts/check_compliance.py`. Outputs are excerpts from real runs.

Exit codes: `0` compliant, `1` violations found, `2` tool error.

## Summary

| # | Scenario | Injection | Detected by | Detection time |
|---|----------|-----------|-------------|----------------|
| 1 | Wrong remote AS | `neighbor 10.0.12.3 remote-as 65099` on r1 | `BGP Peer` + `BGP Session` (r1), `BGP Session` (r2) | < 10 s |
| 2 | Unauthorized neighbor | `neighbor 10.0.12.5 remote-as 65010` on r2 | `Unexpected BGP Peers` (r2) | immediate |
| 3 | Hostname drift | `hostname r3-old` via vtysh and `frr.conf` | not reproducible in the lab (see below) | — |
| 4a | Router stopped | `docker stop netops-r3` | `Reachability` (r3), `BGP Session` (r2) | < 5 s |
| 4b | Frozen control plane | `docker pause netops-r3` | `State Collection` (r3); `BGP Session` (r2) only after hold timer | ~128 s on r2 |

## 1. Wrong remote AS on r1

**Injection**

```bash
docker exec netops-r1 vtysh -c "conf t" -c "router bgp 65001" \
  -c "neighbor 10.0.12.3 remote-as 65099"
```

**Detection** (`--device r1 --device r2`, exit code 1)

```text
Device: r1
[FAIL] BGP Peer
       expected=10.0.12.3 AS65002
       actual=10.0.12.3 AS65099
[FAIL] BGP Session
       expected=10.0.12.3 Established
       actual=10.0.12.3 Idle

Device: r2
[PASS] BGP Peer
       expected=10.0.12.2 AS65001
       actual=10.0.12.2 AS65001
[FAIL] BGP Session
       expected=10.0.12.2 Established
       actual=10.0.12.2 Idle
```

**Device-side confirmation**

```text
r1: Last reset ..., Notification sent (OPEN Message Error/Bad Peer AS)
r2: Last reset ..., Notification received (OPEN Message Error/Bad Peer AS)
```

**Analysis**

- r1 shows the cause (configuration), r2 shows only the symptom (session down,
  configuration correct). Separating configuration checks from operational
  checks points to the device that needs to be fixed.
- The r2–r3 session stayed `Established`: the fault was isolated.

**Recovery**

Restoring `remote-as 65002` fixed the configuration immediately, but the session
came back only about 2 minutes later: after repeated failures FRR waits longer
before retrying. A rollback that only verifies the configuration would have
reported success while the link was still down — post-checks must verify
operational state.

## 2. Unauthorized BGP neighbor on r2

**Injection**

```bash
docker exec netops-r2 vtysh -c "conf t" -c "router bgp 65002" \
  -c "neighbor 10.0.12.5 remote-as 65010"
```

**Detection** (exit code 1) — all other checks on r2 passed:

```text
[FAIL] Unexpected BGP Peers
       expected=<none>
       actual=10.0.12.5 AS65010
       detail=neighbor is not declared in the inventory
```

**Comparison with device discovery** (`scripts/discover_devices.py`):

```text
BGP Peers:    2/3
BGP Health:   UNHEALTHY
Validation:   VALID
```

Discovery only reports that BGP is unhealthy and the legacy validator reports
the device as valid. The compliance engine identifies the actual problem: a
neighbor that should not exist, while all declared sessions are up.

**Recovery:** `no neighbor 10.0.12.5` — compliant again immediately.

## 3. Hostname drift (not reproducible in the lab)

Two injection methods were tried on r3:

1. `hostname r3-old` via `vtysh -c` — the change stayed inside the short-lived
   vtysh process; the FRR daemons kept `r3`.
2. `hostname r3-old` in the bind-mounted `frr.conf` followed by a container
   restart — the daemons still used `r3`.

In both cases the hostname advertised by r3's bgpd (BGP hostname capability,
observed on r2 after a session reset) remained `r3`. In this lab the FRR daemons
inherit the hostname from the container (`hostname:` in Docker Compose).

The engine correctly reported `PASS`: there was no real drift. Hostname drift is
covered by unit tests with simulated state. On real network devices the
hostname is part of the running configuration and the same rule applies.

**Lessons**

- Verify that a fault was actually injected before evaluating detection.
- `frr.conf` is bind-mounted as a single file. Tools that replace the file
  (`sed -i`, `git restore`) create a new inode and the container keeps seeing
  the old content until restart. The file was modified in place
  (`cat tmp > frr.conf`) and restored with `git show HEAD:<path> > <path>`.

## 4a. Router stopped

**Injection:** `docker stop netops-r3`

**Detection** (exit code 1, within 5 seconds):

```text
Device: r2
[FAIL] BGP Session
       expected=10.0.23.3 Established
       actual=10.0.23.3 Connect

Device: r3
[FAIL] Reachability
       expected=10.10.0.13 UP
       actual=10.10.0.13 DOWN
       detail=live state not collected
```

r2 reported `Last reset ..., Peer closed the session`: stopping the container
closed the TCP connection, so r2 did not have to wait for the hold timer.
The r1–r2 session was not affected.

## 4b. Frozen control plane (silent failure)

**Injection:** `docker pause netops-r3` — processes are frozen, TCP connections
stay open, no keepalives are sent.

**Detection on r3** (exit code 1):

```text
[FAIL] State Collection
       expected=device state collected
       actual=collection failed
       detail=Command failed on r3: Error response from daemon:
              Container netops-r3 is paused, unpause the container before exec
```

`Reachability` passed: ICMP echo is answered by the kernel, not by FRR.

**Session state on r2** (hold time 180 s, keepalive 60 s):

```text
15:51:37 r2->r3: BGP state = Established
15:52:08 r2->r3: BGP state = Established
15:52:38 r2->r3: BGP state = Established
15:53:08 r2->r3: BGP state = Established
15:53:38 r2->r3: BGP state = OpenSent
Last reset ..., Notification sent (Hold Timer Expired)
```

**Analysis**

- For about 2 minutes r2 reported a healthy session to a dead router. A
  compliance run limited to r2 would have passed.
- After the hold timer expired, r2 stayed in `OpenSent`: the TCP handshake with
  r3 succeeded (handled by the kernel), but the frozen bgpd never answered the
  OPEN. Network-level reachability does not imply application health.
- The engine is a point-in-time check and detection is bounded by protocol
  timers. Faster detection would require lower BGP timers or BFD.

**Recovery:** `docker unpause netops-r3` — the session was re-established
within seconds.
