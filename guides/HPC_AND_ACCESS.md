# HPC basics and access

## What runs where

A cluster has shared login nodes, compute nodes, storage and a scheduler.
An allocation reserves resources for a limited time. A partition groups nodes
with a particular role or hardware; a credit account pays for allocations.

Use a login node for editing, small setup operations, submission and monitoring.
Use Slurm allocations for CPU work, GPU work, substantial compilation and
long transfers. Requesting more nodes or GPUs does not make an ordinary Python
program distributed. The program must explicitly use those resources.

At KU Leuven, wICE supplies the shared login service and multiple CPU/GPU
partitions. Mindwell uses the same login service and has its own compute
partitions. Genius is historical hardware, not the current login-cluster name.

## Browser access

Open [KU Leuven OnDemand](https://ondemand.hpc.kuleuven.be/) and sign in using
the supported institutional/VSC authentication. Browser use does not require
an SSH key. The portal provides files, login shells, job views and interactive
applications. Read [the OnDemand guide](ONDEMAND.md) before requesting resources.

The login-shell terminal is still a shared login node. A browser tab does not
turn it into an interactive compute allocation.

## SSH from Windows

Use the current official [account and access instructions](https://docs.vscentrum.be/accounts/index.html)
to register the account, configure SSH keys and follow any MFA/certificate
requirements. Windows OpenSSH, MobaXterm and PuTTY have distinct setup paths;
the offline snapshot contains instructions for each. Protect the private key
and keep it outside repositories.

### Location access restrictions (KU Leuven / UHasselt)

Since March 2026, Tier-2 access is governed by the global KU Leuven firewall
rules, and the procedure depends on the laptop:

- **KU Leuven managed laptop:** use MFA (an SSH certificate), both from Belgium
  and from abroad. No additional firewall login is needed.
- **Non-managed laptop:** from all locations (VPN B zone, other VSC universities,
  other Belgian IP addresses and abroad), open
  [firewall.vscentrum.be](https://firewall.vscentrum.be) and request a
  certificate. The firewall page only needs to be active while making new
  connections. Connections from within the VSC network, i.e. other VSC
  clusters, need only the certificate.

The other VSC sites apply their own firewall rules; do not transfer these
Leuven rules to them. Source: source/accounts/authentication.rst, label
location_access_restrictions.

From PowerShell, after configuring authentication:

    ssh YOUR_VSC_LOGIN@login.hpc.kuleuven.be

Use your actual login in place of YOUR_VSC_LOGIN. Do not copy another person's
account or key. An SSH configuration alias can simplify repeated connections,
but its local private-key path belongs in your own SSH configuration.

## A first project session

1. Confirm service availability and sign in.
2. Inspect available accounts and balances with sam-balance.
3. Clone the research project with its submodules into the persistent small-file
   tier selected by the project. Keep large data and weights in its approved
   project-storage locations.
4. Read the project's docs/VSC.md. Confirm the required filesystem, interpreter,
   hardware, inputs, output locations and resume behavior.
5. Stage dependencies, datasets and weights before compute. Network access can
   vary by site and node; do not rely on runtime downloads without verifying it.
6. Start with a bounded CPU/GPU preflight, inspect the log and only then request
   the production allocation.

Do not change or rebuild a populated environment as an incidental setup step.
Do not erase partial results to make a retry appear clean.

## Other VSC sites and Tier-1

The offline source covers Antwerp, Brussels, Ghent, Tier-1 compute, cloud and
data services as well. Their accounts, partitions, quotas, software stacks and
authentication details can differ. Read the corresponding source section
before using them. Leuven examples in this library are not universal VSC commands.

Sources in the offline snapshot: source/accounts/index.rst,
source/accounts/authentication.rst, source/accounts/generating_keys_windows.rst,
source/compute/portal/index.rst and source/leuven/tier2_hardware/tier2_login_nodes.rst.
