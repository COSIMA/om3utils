"""Functions to read and manipulate profiling data."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

import xarray as xr

from om3utils.payu_config_yaml import read_payu_config_yaml


class ProfilingParser(ABC):
    """Abstract parser of profiling data.

    The main purpose of a parser of profiling data is to read said data from a file or directory and return it in a
    standard format.

    Once parsed, the profiling data should be stored in a dict in the following way:

    {
        'region': ['region1', 'region2', ...],
        'metric a': [val1a, val2a, ...],
        'metric b': [val1b, val2b, ...],
        ...
    }

    The 'region' values correspond to the labels of the profile regions. Then, for each metric, there is a list of
    values, one for each profiling region. Therefore, 'val1a', is the value for metric a of region 1.
    """

    def __init__(self):
        pass

    @property
    @abstractmethod
    def metrics(self) -> list:
        """list: Metrics available when using this parser."""

    @abstractmethod
    def read(self, path: Path) -> dict:
        """Given a path, open the corresponding file/directory, parse its contents, and return a dictionary holding the
        profiling data.

        Args:
            path (Path): Path to parse. Can be a file or directory, depending on the parser.

        Returns:
            dict: Profiling data.
        """


def parse_profiling_data(
    run_dirs: list, parser: ProfilingParser, varname: str, getvar: Callable[[Path], int]
) -> xr.Dataset:
    """Given a list of directories containing profiling data, parse the data and return it as a xarray dataset.

    Args:
        run_dirs (list): Directories to parse.
        parser (ProfilingParser): Instance of the parser to use.
        varname (str): Name of the variable that changes between run directories.
        getvar (Callable): Callback function to extract the value of the variable that changes between run directories.

    Returns:
        Dataset: Profiling data.
    """
    datasets = []
    for run_dir in [Path(path) for path in run_dirs]:
        data = parser.read(run_dir)
        datasets.append(
            xr.Dataset(
                data_vars=dict(
                    zip(
                        parser.metrics,
                        [xr.DataArray([data[metric]], dims=[varname, "region"]) for metric in parser.metrics],
                    )
                ),
                coords={"region": data["region"], varname: [getvar(run_dir)]},
            )
        )

    # Create dataset with all the data
    return xr.concat(datasets, dim=varname)
