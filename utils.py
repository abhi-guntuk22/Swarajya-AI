"""
utils.py — Hardware Monitoring & Networking Utilities
Swarajya-AI system introspection layer.

Provides real-time metrics without crashing if hardware libs are absent.
"""

import socket
import platform
import psutil
import time
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# 🖥️ Hardware Metrics
# ─────────────────────────────────────────────

@dataclass
class HardwareMetrics:
    """Snapshot of system resource usage."""
    cpu_percent: float = 0.0
    cpu_cores: int = 0
    cpu_freq_mhz: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    ram_percent: float = 0.0
    gpu_available: bool = False
    gpu_name: str = "Not detected"
    vram_used_gb: float = 0.0
    vram_total_gb: float = 0.0
    vram_percent: float = 0.0
    gpu_utilization: float = 0.0
    disk_free_gb: float = 0.0
    disk_total_gb: float = 0.0
    collected_at: float = field(default_factory=time.time)


def get_hardware_metrics() -> HardwareMetrics:
    """
    Collect system hardware metrics.
    Gracefully degrades if GPU libs are not available.
    """
    metrics = HardwareMetrics()

    try:
        metrics.cpu_percent = psutil.cpu_percent(interval=0.2)
        metrics.cpu_cores = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq()
        metrics.cpu_freq_mhz = round(freq.current, 1) if freq else 0.0
    except Exception:
        pass

    try:
        ram = psutil.virtual_memory()
        metrics.ram_used_gb = round(ram.used / (1024 ** 3), 2)
        metrics.ram_total_gb = round(ram.total / (1024 ** 3), 2)
        metrics.ram_percent = ram.percent
    except Exception:
        pass

    try:
        disk = psutil.disk_usage("/")
        metrics.disk_free_gb = round(disk.free / (1024 ** 3), 1)
        metrics.disk_total_gb = round(disk.total / (1024 ** 3), 1)
    except Exception:
        pass

    try:
        import torch
        if torch.cuda.is_available():
            metrics.gpu_available = True
            metrics.gpu_name = torch.cuda.get_device_name(0)
            vram_total = torch.cuda.get_device_properties(0).total_memory
            vram_reserved = torch.cuda.memory_reserved(0)
            metrics.vram_total_gb = round(vram_total / (1024 ** 3), 2)
            metrics.vram_used_gb = round(vram_reserved / (1024 ** 3), 2)
            if metrics.vram_total_gb > 0:
                metrics.vram_percent = round(
                    (metrics.vram_used_gb / metrics.vram_total_gb) * 100, 1
                )
    except ImportError:
        _try_pynvml(metrics)
    except Exception:
        _try_pynvml(metrics)

    if metrics.gpu_available:
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            metrics.gpu_utilization = float(util.gpu)
        except Exception:
            pass

    return metrics


def _try_pynvml(metrics: HardwareMetrics):
    """Fallback GPU detection via pynvml (no PyTorch required)."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        metrics.gpu_available = True
        metrics.gpu_name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(metrics.gpu_name, bytes):
            metrics.gpu_name = metrics.gpu_name.decode()
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        metrics.vram_total_gb = round(mem.total / (1024 ** 3), 2)
        metrics.vram_used_gb = round(mem.used / (1024 ** 3), 2)
        if metrics.vram_total_gb > 0:
            metrics.vram_percent = round(
                (metrics.vram_used_gb / metrics.vram_total_gb) * 100, 1
            )
    except Exception:
        pass


# ─────────────────────────────────────────────
# 🌐 Network Utilities
# ─────────────────────────────────────────────

def get_local_ip() -> str:
    """
    Detect the machine's LAN IPv4 address.
    Uses a UDP trick that requires no actual packet transmission.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        addrs = socket.getaddrinfo(hostname, None, socket.AF_INET)
        for addr in addrs:
            ip = addr[4][0]
            if not ip.startswith("127."):
                return ip
    except Exception:
        pass

    return "127.0.0.1"


def get_system_info() -> dict:
    """Return basic OS/platform information."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "hostname": socket.gethostname(),
    }


# ─────────────────────────────────────────────
# 🎨 UI Helpers
# ─────────────────────────────────────────────

def percent_to_color(percent: float) -> str:
    """Return a CSS color based on usage percentage."""
    if percent < 50:
        return "#00d68f"
    if percent < 80:
        return "#ffaa00"
    return "#ff3d71"


def format_gb(value_gb: float) -> str:
    """Format gigabyte values for display."""
    if value_gb < 1:
        return f"{value_gb * 1024:.0f} MB"
    return f"{value_gb:.1f} GB"
