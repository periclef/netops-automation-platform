# NetOps Automation Platform

A modular network automation platform designed to automate network discovery, configuration management, operational state collection, validation, and troubleshooting.

## Project Status

> 🚧 Work in progress — this project is being built incrementally as part of a hands-on NetOps / Network Automation portfolio.

## Goals

The platform is designed to provide a foundation for:

- Network device inventory management
- Automated device discovery
- Operational state collection
- Configuration backup
- Configuration generation and deployment
- Network state validation
- Configuration drift detection
- Failure detection and troubleshooting
- Logging and audit trails
- Automated testing and CI/CD

## Architecture

The project follows a modular Python architecture:

```text
                    NetOps Platform
                          |
          +---------------+---------------+
          |               |               |
      Inventory        Drivers        Validation
          |               |               |
          +-------- Device Manager --------+
                          |
                  Automation Engine
                          |
                 Network Infrastructure
Lab Environment

The development lab runs locally on Ubuntu Server using open-source networking technologies.

Network infrastructure will be simulated using technologies such as:

Docker / Docker Compose
FRRouting (FRR)
Linux networking
Network namespaces
Linux bridges
veth interfaces
VLAN / VRF
iproute2
nftables
tc/netem

No physical network devices or commercial Cisco/Juniper virtual images are required.

Lab vs. Production

The lab implementation is intentionally based on Linux and open-source networking technologies.

Production environments could integrate the same automation concepts with enterprise platforms such as Cisco IOS-XE/NX-OS, Juniper Junos, Arista EOS, or other network operating systems.

Possible management interfaces include:

SSH
NETCONF
RESTCONF
REST APIs
SNMP
Syslog
gNMI / streaming telemetry

Vendor-specific production examples included in this repository should be considered conceptual reference implementations unless explicitly marked as tested.

Technology Stack

Initial technologies:

Python
Git
Docker
Docker Compose
Ubuntu Server

Additional technologies will be introduced only when required by the implementation.

Repository Structure
netops-automation-platform/
├── docs/
├── src/
│   └── netops/
├── tests/
├── .github/
│   └── workflows/
├── .env.example
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md

The repository structure will evolve as the platform is implemented.

Development Approach

The project is developed incrementally:

Build the foundation
Create the network lab
Implement inventory management
Establish device connectivity
Collect and normalize network state
Implement configuration management
Validate network state
Introduce controlled failure scenarios
Add automated testing
Add CI/CD
Document lab and production architectures
Security

Secrets, credentials, API keys, and environment-specific configuration must not be committed to the repository.

Environment variables and local secrets will be excluded through .gitignore, with .env.example used only as a safe configuration template.

License

This project will be released under the MIT License.
