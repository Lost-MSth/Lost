import dataclasses

@dataclasses.dataclass
class TPUSpec:
    """
    Specification of the KDT-TPU architecture.
    """

    num_sms: int
    load_store_latency: int # Latency (in cycles) for load/store operations, analogous to $L_{mem}$ in statement.md
    spm_size: int = 1024 * 1024  # Size of the SPM (in bytes) per SM
    vxm_trpt: int = 128
    mxm_trpt: int = 2048
    