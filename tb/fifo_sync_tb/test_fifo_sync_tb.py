from hdlworkflow import HdlWorkflow
import os
import pytest


@pytest.mark.parametrize("data_width", [1, 8, 16, 32])
@pytest.mark.parametrize("depth", [8, 32, 256, 1024])
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
        eda_tool="nvc",
        top="fifo_sync",
        path_to_compile_order="compile_order.txt",
        path_to_working_directory=pwd,
        generic=generics,
        cocotb="fifo_sync_tb",
        pythonpaths=[pwd],
    )
    workflow.run()
