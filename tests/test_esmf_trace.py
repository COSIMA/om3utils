import pytest

bt2 = pytest.importorskip("bt2", reason="Requires babeltrace2 python bindings")

from om3utils.esmf_trace import SinglePETTimingNode, MultiPETTimingNode


@pytest.fixture()
def tree_nodes():
    def _tree_nodes(_id: [int], pet: [int], name: [str]):
        node1 = SinglePETTimingNode(_id[0], pet[0], name[0])
        node2 = SinglePETTimingNode(_id[1], pet[1], name[1])
        node3 = SinglePETTimingNode(_id[2], pet[2], name[2])
        return node1, node2, node3

    return _tree_nodes


@pytest.fixture()
def single_pet_tree_nodes(tree_nodes):
    return tree_nodes([0, 1, 2], [10, 10, 10], ["region_a", "region_b", "region_c"])


def test_single_timing_node():
    node = SinglePETTimingNode(2, 10, "region_a")
    node.total = 10.0
    node.count = 8
    node.min = 5.1
    node.max = 50.5
    node.mean = 20.8

    assert node.name == "region_a"
    assert node.pet == 10
    assert node.total == 10.0
    assert node.count == 8
    assert node.min == 5.1
    assert node.max == 50.5
    assert node.mean == 20.8
    assert node.children == []


def test_single_timing_node_add_child():
    root = SinglePETTimingNode(0, 10, "region_a")
    child = SinglePETTimingNode(1, 10, "region_b")

    assert root.add_child(0, child)
    assert root.children == [child]


def test_single_timing_node_add_child_not_root():
    node = SinglePETTimingNode(2, 10, "region_a")

    with pytest.raises(KeyError):
        node.add_child(2, SinglePETTimingNode(1, 10, "region_b"))


def test_single_timing_node_tree(single_pet_tree_nodes):
    root, child1, child2 = single_pet_tree_nodes
    root.add_child(0, child1)
    root.add_child(1, child2)

    assert root.children == [child1]
    assert child1.children == [child2]


def test_single_timing_node_incorrect_tree(single_pet_tree_nodes):
    root, child1, child2 = single_pet_tree_nodes

    root.add_child(0, child1)

    with pytest.raises(KeyError):
        root.add_child(2, child2)


@pytest.fixture()
def multi_pet_nodes(tree_nodes):
    node1, node2, node3 = tree_nodes([0, 0, 0], [1, 2, 3], ["region", "region", "region"])
    node1.total = 50.0
    node2.total = 55.0
    node3.total = 45.0
    node1.count = 5
    node2.count = 5
    node3.count = 5
    node1.min = 9.0
    node2.min = 10.0
    node3.min = 8.0
    node1.max = 11.5
    node2.max = 12.5
    node3.max = 9.5
    return node1, node2, node3


@pytest.fixture()
def multi_timing_tree(tree_nodes):
    trees = []
    for tree_id in range(3):
        node1, node2, node3 = tree_nodes([0, 1, 2], [tree_id] * 3, ["region_a", "region_b", "region_c"])
        node1.add_child(0, node2)
        node1.add_child(1, node3)
        trees.append(node1)

    return trees[0], trees[1], trees[2]


def test_simple_multi_timing_node(multi_pet_nodes):
    node1, node2, node3 = multi_pet_nodes

    multi = MultiPETTimingNode()
    multi.merge(node1)
    multi.merge(node2)
    multi.merge(node3)

    assert multi.pet_count == 3
    assert multi.counts_match and multi.count_each == 5

    assert multi.total_sum == 150.0
    assert multi.total_sum_s == 0.000000150

    assert multi.total_min == 8.0
    assert multi.total_min_s == 0.000000008
    assert multi.total_min_pet == 3

    assert multi.total_max == 12.5
    assert multi.total_max_s == 0.0000000125
    assert multi.total_max_pet == 2

    assert multi.total_mean == 50.0
    assert multi.total_mean_s == 0.00000005


def test_multi_timing_node_no_count_match(multi_pet_nodes):
    node1, node2, node3 = multi_pet_nodes
    node2.count = 4

    multi = MultiPETTimingNode()
    multi.merge(node1)
    multi.merge(node2)
    multi.merge(node3)

    assert not multi.counts_match


def test_multi_timing_tree(multi_timing_tree):
    multi = MultiPETTimingNode()
    tree1, tree2, tree3 = multi_timing_tree

    multi.merge(tree1)
    multi.merge(tree2)
    multi.merge(tree3)

    assert multi.pet_count == 3
    assert multi.children["region_b"].pet_count == 3
    assert multi.children["region_b"].children["region_c"].pet_count == 3
