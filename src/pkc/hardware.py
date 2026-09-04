"""Hardware- und Systemerkennung fuer die Modellprofilwahl.

Bewusst ohne externe Abhaengigkeiten: alles wird ueber die Standardbibliothek
bzw. optional vorhandene Systemwerkzeuge ermittelt.  Werte, die nicht sicher
bestimmt werden koennen, bleiben ``None`` - sie werden nicht geraten.
"""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class HardwareInfo:
    os_name: str
    os_version: str
    machine: str
    python_version: str
    cpu_name: str | None
    cpu_cores: int | None
    ram_total_gb: float | None
    gpu_name: str | None
    vram_gb: float | None
    free_disk_gb: float | None
    root_writable: bool

    def as_dict(self) -> dict:
        return asdict(self)


def _ram_gb() -> float | None:
    # Linux/Unix
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if pages > 0 and page_size > 0:
            return round(pages * page_size / 1024**3, 1)
    except (ValueError, OSError, AttributeError):
        pass
    # Windows
    if platform.system() == "Windows":  # pragma: no cover - nur Windows
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        try:
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return round(status.ullTotalPhys / 1024**3, 1)
        except OSError:
            return None
    return None


def _cpu_name() -> str | None:
    system = platform.system()
    if system == "Linux":
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
        except OSError:
            pass
    elif system == "Windows":  # pragma: no cover - nur Windows
        name = os.environ.get("PROCESSOR_IDENTIFIER")
        if name:
            return name
    return platform.processor() or None


def _gpu() -> tuple[str | None, float | None]:
    """Fragt nvidia-smi ab, falls vorhanden. Kein Raten."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None, None
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return None, None
    line = out.stdout.strip().splitlines()[0] if out.stdout.strip() else ""
    if not line:
        return None, None
    parts = [p.strip() for p in line.split(",")]
    name = parts[0] if parts else None
    vram = None
    if len(parts) > 1:
        try:
            vram = round(float(parts[1]) / 1024, 1)
        except ValueError:
            vram = None
    return name, vram


def detect(root: Path) -> HardwareInfo:
    gpu_name, vram = _gpu()
    try:
        free = round(shutil.disk_usage(root).free / 1024**3, 1)
    except OSError:
        free = None
    writable = False
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".hwtest"
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
        writable = True
    except OSError:
        writable = False
    return HardwareInfo(
        os_name=platform.system(),
        os_version=platform.version(),
        machine=platform.machine(),
        python_version=platform.python_version(),
        cpu_name=_cpu_name(),
        cpu_cores=os.cpu_count(),
        ram_total_gb=_ram_gb(),
        gpu_name=gpu_name,
        vram_gb=vram,
        free_disk_gb=free,
        root_writable=writable,
    )


#: Modellprofile: Empfehlung anhand RAM/VRAM.
PROFILES = {
    "light": {
        "label": "LIGHT",
        "min_ram_gb": 6,
        "description": "3B-Klasse, Q4 quantisiert, CPU-tauglich, geringste Qualitaet",
        "suggested_context": 4096,
    },
    "standard": {
        "label": "STANDARD",
        "min_ram_gb": 12,
        "description": "7-8B-Klasse, Q4_K_M, guter Kompromiss fuer Buerorechner",
        "suggested_context": 8192,
    },
    "high": {
        "label": "HIGH QUALITY",
        "min_ram_gb": 24,
        "description": "12-14B-Klasse, Q5/Q6, beste Fachqualitaet, GPU empfohlen",
        "suggested_context": 16384,
    },
}


def recommend_profile(info: HardwareInfo) -> str:
    """Konservative Empfehlung. Ohne RAM-Information -> 'light'."""
    ram = info.ram_total_gb
    if ram is None:
        return "light"
    if ram >= PROFILES["high"]["min_ram_gb"]:
        return "high"
    if ram >= PROFILES["standard"]["min_ram_gb"]:
        return "standard"
    return "light"
