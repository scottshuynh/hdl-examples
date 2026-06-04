import os
import pytest
import subprocess
from pathlib import Path
from hdlworkflow import HdlWorkflow


@pytest.fixture(scope="module")
def setup_flow():
    try:
        test_working_dir = Path(__file__).parent
        os.chdir(test_working_dir)

        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        hdldepends_proc = subprocess.run(
            [
                "hdldepends",
                f"{repo_root}/hdldepends_config.toml",
                "--top-entity",
                "fifo_sync",
                "--compile-order-vhdl-lib",
                "work:compile_order.txt",
            ]
        )
        assert hdldepends_proc.returncode == 0

    except subprocess.CalledProcessError:
        raise subprocess.SubprocessError

    flow_cfg = dict()
    flow_cfg["pwd"] = test_working_dir
    flow_cfg["compile_order"] = test_working_dir / "compile_order.txt"
    flow_cfg["pythonpaths"] = [str(test_working_dir)]
    return flow_cfg


@pytest.mark.parametrize("DATA_W", [1, 8, 11, 16, 32])
@pytest.mark.parametrize("DEPTH", [8, 32, 256, 1024, 1337])
@pytest.mark.parametrize("IS_FWFT", [False, True])
@pytest.mark.prod
def test_fifo_sync_tb(setup_flow, DATA_W: int, DEPTH: int, IS_FWFT: bool, worker_id):
    """
    Simulate fifo_sync for all elaborated permutations specified.
    """
    generics = [f"{DATA_W=}", f"{DEPTH=}", f"{IS_FWFT=}"]
    pwd = os.path.dirname(__file__)
    print(f"pwd: {pwd}")
    workflow = HdlWorkflow(
        eda_tool="nvc",
        top="fifo_sync",
        compile_order=setup_flow["compile_order"],
        path_to_working_directory=setup_flow["pwd"] / "artefacts" / worker_id,
        generics=generics,
        cocotb="fifo_sync_tb",
        pythonpaths=setup_flow["pythonpaths"],
    )
    workflow.run()


@pytest.mark.parametrize("DATA_W", [8])
@pytest.mark.parametrize("DEPTH", [32])
@pytest.mark.parametrize("IS_FWFT", [True])
@pytest.mark.gui
def test_fifo_sync_gui_tb(
    setup_flow, DATA_W: int, DEPTH: int, IS_FWFT: bool, worker_id
):
    """
    Simulate fifo_sync for all elaborated permutations specified.
    Opens gtkwave on completion.
    """
    generics = [f"{DATA_W=}", f"{DEPTH=}", f"{IS_FWFT=}"]
    pwd = os.path.dirname(__file__)
    print(f"pwd: {pwd}")
    workflow = HdlWorkflow(
        eda_tool="nvc",
        top="fifo_sync",
        compile_order=setup_flow["compile_order"],
        path_to_working_directory=setup_flow["pwd"] / "artefacts" / worker_id,
        generics=generics,
        cocotb="fifo_sync_tb",
        pythonpaths=setup_flow["pythonpaths"],
        gui=True,
    )
    workflow.run()
