"""Classes to represent timing trees as produced by ESMF when running in profiling mode.

ESMF can output an execution trace using the Common Trace Format (CTF). Full CTF documentation can be found online at
https://diamon.org/ctf/, but in a nutshell, CFT is a very flexible binary trace format. A reference parser
implementation of CTF is provided by the Babeltrace 2 library (https://babeltrace.org/), which also includes Python 3
bindings.

Note that most of the contents of this file are based on the code from esmf-profiler (https://github.com/esmf-org/esmf-profiler).
"""

import sys
from pathlib import Path

import bt2

from om3utils.utils import nano_to_sec


class SinglePETTimingNode:
    """Representation of a single PET timing node in a tree of profiling events.

    One node corresponds to one profiling region and one PET (Persistent Execution Thread) and it can have
    child regions, which are store in a list. This allows to create a tree of regions.

    Furthermore, the root node of a tree (id = 0) also stores a dictionary of all the regions that exist in that tree.
    This allows to efficiently append a new node to the tree.
    """

    def __init__(self, _id: int, pet: int, name: str):
        """

        Args:
            _id (int): Region ID.
            pet (int): PET number.
            name (str): Region name.
        """
        self._id = _id
        self._pet = pet
        self._name = name
        self._total = 0
        self._min = sys.maxsize
        self._max = 0
        self._mean = 0
        self._count = 0
        self._children = []  # Children that have this node as direct parent

        # Cache containing all of this node's children, direct or indirect, that is, all the nodes that belong to the
        # tree that have this node as root. Note that only the root node of the tree maintains a cache (self._id = 0)
        self._child_cache = {}  # id -> SinglePetTimingTreeNode
        if self._id == 0:
            self._child_cache[self._id] = self

    @property
    def name(self):
        """str: Name of profiling region."""
        return self._name

    @property
    def pet(self):
        """int: PET number."""
        return self._pet

    @property
    def total(self):
        """float: Total time spent in the region, in nanoseconds."""
        return self._total

    @total.setter
    def total(self, value):
        self._total = value

    @property
    def count(self):
        """int: Number of times this region was executed."""
        return self._count

    @count.setter
    def count(self, value):
        self._count = value

    @property
    def min(self):
        """float: Minimum time spent in the region, in nanoseconds."""
        return self._min

    @min.setter
    def min(self, value):
        self._min = value

    @property
    def max(self):
        """float: Maximum time spent in the region, in nanoseconds."""
        return self._max

    @max.setter
    def max(self, value):
        self._max = value

    @property
    def mean(self):
        """float: Mean time spent in the region, in nanoseconds."""
        return self._mean

    @mean.setter
    def mean(self, value):
        self._mean = value

    @property
    def children(self):
        """list: Children that have this node as direct parent"""
        return self._children

    #
    def add_child(self, parentid, child: "SinglePETTimingNode"):
        """Add child node to the node with given parentid.

        Note that it must be called only from the root of the tree (self._id == 0).

        Args:
            parentid (int): Parent region ID.
            child (SinglePETTimingNode): Child to add.

        Returns:
            bool: Execution status.
        """
        self._child_cache[parentid]._children.append(child)
        self._child_cache[child._id] = child
        return True


class MultiPETTimingNode:
    """Representation of a multi-PET timing node in a tree of profiling events.

    One node corresponds to one profiling region executed by one or more PETs. The tree is constructed by merging
    single-PET timing trees. The multi-PET statistics are computed and updated every time a new single-PET timing tree
    is merged into the multi-PET tree.
    """

    def __init__(self):
        self._children: dict[str, MultiPETTimingNode] = (
            {}
        )  # sub-regions in the timing tree  { name -> MultiPETTimingNode }
        self._pet_count = 0  # the number of PETs reporting timing information for this node
        self._count_each = -1  # how many times each PET called into this region
        self._counts_match = True  # if counts_each is not the same for all reporting PETs, then this is False
        self._total_sum = 0  # sum of all totals
        self._total_min = sys.maxsize  # min of all totals
        self._total_min_pet = -1  # PET with min total
        self._total_max = 0  # max of all totals
        self._total_max_pet = -1  # PET with max total
        self._contributing_nodes = {}  # map of contributing SinglePETTimingNodes (key = PET)

    @property
    def pet_count(self):
        """int: Number of PETs reporting timing information for this node."""
        return self._pet_count

    @property
    def count_each(self):
        """int: How many times each PET is called into this region.

        Note that this value is only meaningful if self.counts_match is true.
        """
        return self._count_each

    @property
    def counts_match(self):
        """bool: Is the value of counts_each the same for all reporting PETs?"""
        return self._counts_match

    @property
    def total_sum(self):
        """float: Sum of all totals from all PETs, in nanoseconds."""
        return self._total_sum

    @property
    def total_sum_s(self):
        """float: Sum of all totals from all PETs, in seconds."""
        return nano_to_sec(self._total_sum)

    @property
    def total_mean(self):
        """float: The mean total time, averaged over all PETs, in nanoseconds."""
        return self._total_sum / self._pet_count

    @property
    def total_mean_s(self):
        """float: The mean total time, averaged over all PETs, in seconds."""
        return nano_to_sec(self.total_mean)

    @property
    def total_min(self):
        """float: Minimum total time spend in this region among all PETs, in nanoseconds."""
        return self._total_min

    @property
    def total_min_s(self):
        """float: Minimum total time spend in this region among all PETs, in seconds."""
        return nano_to_sec(self._total_min)

    @property
    def total_min_pet(self):
        """int: ID of PET who spent the minimum total time in this region."""
        return self._total_min_pet

    @property
    def total_max(self):
        """float: Maximum total time spend in this region among all PETs, in nanoseconds."""
        return self._total_max

    @property
    def total_max_s(self):
        """float: Maximum total time spend in this region among all PETs, in seconds."""
        return nano_to_sec(self._total_max)

    @property
    def total_max_pet(self):
        """int: ID of PET who spent the maximum total time in this region."""
        return self._total_max_pet

    @property
    def children(self):
        """dict[str, MultiPETTimingNode]: Direct children of this node."""
        return self._children

    def _merge_children(self, other: SinglePETTimingNode):
        for c in other.children:
            rs = self._children.setdefault(c.name, MultiPETTimingNode())
            rs.merge(c)

    def merge(self, other: SinglePETTimingNode):
        """Merge a single-PET tree into this multi-PET timing tree.

        Update the statistics of this MultiPETTimingNode by including the information from a new SinglePETTiming node.
        This function then proceeds to traverse the entire single-PET tree and merge all of its nodes. This is achieved
        by calling the self._merge_children method.

        Args:
            other (SinglePETTimingNode): Single-PET tree to merge.
        """
        self._pet_count += 1
        if self._pet_count == 1:
            self._count_each = other.count
        elif self._count_each != other.count:
            self._counts_match = False

        self._total_sum += other.total
        if self._total_min > other.min:
            self._total_min = other.min
            self._total_min_pet = other.pet
        if self._total_max < other.max:
            self._total_max = other.max
            self._total_max_pet = other.pet

        self._contributing_nodes[other.pet] = other

        self._merge_children(other)


class ESMFTrace:
    """Tree of MultiPetTimingNodes constructed by parsing the traces generated by ESMF.

    Args:
        path (str): Directory containing the traces to parse.
    """

    def __init__(self, path: Path):
        self._region_id_to_name_map = {}  # { pet -> { region_id -> region name } }
        self._timing_trees = {}  # { pet -> root of timing tree }
        self._regions = {"TOP"}  # Set containing all known regions. Using a set ensures region's names are unique.

        # Iterate over the trace messages.
        for msg in bt2.TraceCollectionMessageIterator(path.as_posix()):
            if type(msg) is bt2._EventMessageConst:
                self._handle_event(msg)

        self.multiPETTree = MultiPETTimingNode()
        for _, t in self._timing_trees.items():
            self.multiPETTree.merge(t)

    @property
    def regions(self) -> list[str]:
        """list[str]: Name of all the known regions."""
        return list(self._regions)

    def _handle_event(self, msg: bt2._EventMessageConst):
        """Process a trace event message, extracting and storing any relevant information.

        Args:
            msg (bt2._EventMessageConst: Trace message describing the event to handle.
        """
        if msg.event.name == "define_region":
            pet = int(msg.event.packet.context_field["pet"])
            regionid = int(msg.event.payload_field["id"])
            name = str(msg.event.payload_field["name"])
            self._region_id_to_name_map.setdefault(pet, {})[regionid] = name
            self._regions.add(name)

        elif msg.event.name == "region_profile":
            pet = int(msg.event.packet.context_field["pet"])
            region_id = int(msg.event.payload_field["id"])
            parent_id = int(msg.event.payload_field["parentid"])

            if region_id == 1:
                # special case for outermost timed region
                name = "TOP"
            else:
                _map = self._region_id_to_name_map[pet]
                name = _map[region_id]  # should already be there

            node = SinglePETTimingNode(region_id, pet, name)
            node.total = int(msg.event.payload_field["total"])
            node.count = int(msg.event.payload_field["count"])
            node.min = int(msg.event.payload_field["min"])
            node.max = int(msg.event.payload_field["max"])

            # add child to the timing tree for the given pet
            root = self._timing_trees.setdefault(pet, SinglePETTimingNode(0, pet, "TOP_LEVEL"))
            if not root.add_child(parent_id, node):
                raise RuntimeError(
                    f"{self.__class__.__name__} child not added to tree pet = {pet}, regionid = {region_id}, parentid = {parent_id}, name = {name}"
                )
