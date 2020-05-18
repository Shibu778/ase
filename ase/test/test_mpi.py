import numpy as np

from ase.parallel import world, new_world, DummyMPI, dummy


def test_mpi():
    """Exercise ase.parallel module."""
    myworld = DummyMPI()
    with new_world(myworld):
        assert world.comm is myworld
    assert world.comm is dummy
    assert world.sum(1) == 1
    a = np.ones(5)
    world.sum(a)
    assert a.sum() == 5
    assert world.rank == 0
    assert world.size == 1