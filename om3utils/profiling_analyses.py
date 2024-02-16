from pathlib import Path
import xarray as xr

from om3utils.payu_config_yaml import read_payu_config_yaml


def scaling_ncpus(run_dir):
    """Extract the number of CPUs (or cores) used in a given profiling run. This is meant to be use when parsing scaling
    data, that is, extracting data that depends on the number of CPUs.

    Args:
        run_dir (Path): Directory containing the profiling data.

    Returns:
         int: Number of CPUs.
    """
    config_file = Path(run_dir) / "config.yaml"
    config = read_payu_config_yaml(config_file.as_posix())
    return config["ncpus"]


def scaling_speedup(stats: xr.Dataset) -> xr.Dataset:
    """Calculates the parallel speedup from scaling data.

    Args:
        stats (Dataset): Scaling data, stored as a xarray dataset.

    Returns:
        Dataset: Parallel speedup.
    """
    speedup = stats.tavg.sel(ncpus=stats["ncpus"].min()) / stats.tavg
    speedup.name = "speedup"
    return speedup


def scaling_efficiency(stats: xr.Dataset) -> xr.Dataset:
    """Calculates the parallel efficiency from scaling data.

    Args:
        stats (Dataset): Scaling data, stored as a xarray dataset.

    Returns:
        Dataset: Parallel efficiency.
    """
    speedup = scaling_speedup(stats)
    eff = speedup / speedup.ncpus * 100 * stats["ncpus"].min()
    eff.name = "parallel efficiency [%]"
    return eff
