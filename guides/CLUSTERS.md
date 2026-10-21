# Clusters and resource selection

Read [UPSTREAM_CHANGES.md](../UPSTREAM_CHANGES.md) for source-review flags.
The table reflects the reviewed source revision recorded in
[sources.json](../sources.json), not a real-time inventory of available nodes.

## Leuven CPU and GPU choices

| Cluster | Partition | Main role |
|---|---|---|
| wICE | batch / batch_icelake | CPU work; Ice Lake nodes have 72 cores |
| wICE | batch_sapphirerapids | CPU work; Sapphire Rapids nodes have 96 cores |
| Mindwell | batch_graniterapids | CPU work; Granite Rapids nodes have 192 cores |
| wICE | bigmem | Ice Lake nodes with 2 TiB RAM; default 28,000 MiB per core |
| wICE | hugemem | One Ice Lake node with 8 TiB RAM; default 111,900 MiB per core |
| Mindwell | bigmem | Large host-memory CPU jobs; nodes with 1.5 TiB RAM |
| wICE | gpu_p100 | P100, 16 GiB GPU memory |
| wICE | gpu_v100 | V100, 32 GiB GPU memory |
| wICE | gpu_a100 / gpu | A100, 80 GiB GPU memory |
| wICE | gpu_h100 | H100, 80 GiB GPU memory |
| Mindwell | gpu_b200 | B200, 192 GiB GPU memory |
| wICE / Mindwell | interactive | Small interactive development and visualization |

Genius is retired from the current portal selection. The P100/V100 partitions
are on wICE. Explicitly select the cluster when submitting a job.

Regular compute/GPU walltime is generally at most 72 hours. Documented
_long partitions permit up to 168 hours, including wICE P100/V100 long queues.
Do not invent A100/H100/B200 _long names: inspect the actual source or sinfo.
wICE gpu_a100_debug and gpu_p100_debug allow up to one hour. You can have only
a single gpu_a100_debug job in the queue at any time.

The big-memory partitions are charged at higher per-core rates than regular
Ice Lake/Granite Rapids cores; see [credits](OPERATIONS.md#credits).

The interactive partitions allow up to 16 hours and eight CPU cores. wICE
offers at most one A100 MIG slice with one seventh of the device resources,
not a whole 80 GiB GPU. Mindwell's interactive GPU is an RTX 5000 Ada with
32 GiB. A small interactive allocation is not representative of a full A100
or a B200 production job.

## CPU resources per allocated GPU

| Cluster / partition | Maximum cores per GPU | Maximum host memory per GPU (MiB) |
|---|---:|---:|
| wICE gpu_p100* | 9 | 45,000 |
| wICE gpu_v100* | 4 | 84,000 |
| wICE gpu_a100 / gpu | 18 | 126,000 |
| wICE gpu_h100 | 16 | 187,200 |
| Mindwell gpu_b200 | 24 | 194,400 |

These are ceilings, not recommended minimum requests. Request enough CPU
workers and RAM for the measured workload. A job may share the node with
other jobs, while retaining exclusive access to its allocated GPUs and cores.

Host RAM is distinct from VRAM. Slurm can allocate additional CPU cores to
satisfy host-memory requests, affecting both availability and credits.
Use the documented MB/MiB limits carefully: a G suffix is 1024 MiB, so a
rounded-looking request can cross a per-core threshold.

## Choosing a device

Measure peak VRAM, peak host RAM, time spent preparing inputs and actual GPU
utilization on a representative bounded task. A newer GPU does not fix a CPU
data-loading bottleneck or a job waiting on storage.

P100, V100, A100, H100 and B200 require compatible application binaries and
CUDA kernels. In particular, software built before Blackwell support may
not run on B200 simply because CUDA is visible. Test the exact application
and required precision/operations. Driver changes do not upgrade a Python wheel.

Multi-GPU and multi-node runs need an explicitly distributed application.
The source documents different interconnects; wICE H100 nodes use Ethernet
rather than the same InfiniBand arrangement as other groups. Do not infer
cross-node scaling from single-node results.

Sources: source/leuven/wice_quick_start.rst,
source/leuven/mindwell_quick_start.rst,
source/leuven/tier2_hardware/wice_hardware.rst,
source/leuven/tier2_hardware/mindwell_hardware.rst and
source/leuven/slurm_specifics.rst.
