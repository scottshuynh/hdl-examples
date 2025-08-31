from hdlworkflow import HdlWorkflow
import os
import pytest
import random


@pytest.mark.parametrize("data_width", random.sample(range(1, 513), 4))
@pytest.mark.parametrize("depth", random.sample(range(8, 32769), 4))
def test_fifo_sync_tb(data_width: int, depth: int):
    """Parametrized with pytest, generate 4 random values for generics:
    data_width and depth.

    Runs hdlworkflow to simulate fifo_sync for all permutations
    of the generated random generics.

    Args:
        data_width (int): DUT generic: DATA_W
        depth (int): DUT generic: DEPTH
    """
    generics = [f"DATA_W={data_width}", f"DEPTH={depth}"]
    pwd = os.path.dirname(__file__)
    print(f"pwd: {pwd}")
    workflow = HdlWorkflow(
        "nvc",
        "fifo_sync",
        "compile_order.txt",
        pwd,
        generics,
        "fifo_sync_tb",
        [pwd],
    )
    workflow.run()
