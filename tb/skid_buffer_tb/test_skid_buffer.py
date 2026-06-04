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
                "skid_buffer",
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


@pytest.mark.parametrize("DATA_W", [1, 8, 11, 72, 256])
@pytest.mark.parametrize("DEPTH", range(2, 9))
@pytest.mark.parametrize("rand_ce", [True])
@pytest.mark.parametrize("rand_rdy", [True])
@pytest.mark.prod
def test_skid_buffer_tb(
    setup_flow, DATA_W: int, DEPTH: int, rand_ce: bool, rand_rdy: bool, worker_id
):
    """
    Simulate skid_buffer for all elaborated permutations specified.
    """
    generics = [f"{DATA_W=}", f"{DEPTH=}"]
    pwd = os.path.dirname(__file__)
    print(f"pwd: {pwd}")
    workflow = HdlWorkflow(
        eda_tool="nvc",
        top="skid_buffer",
        compile_order=setup_flow["compile_order"],
        path_to_working_directory=setup_flow["pwd"] / "artefacts" / worker_id,
        generics=generics,
        cocotb="skid_buffer_tb",
        plusargs=[
            "rand_ce" if rand_ce else "",
            "rand_rdy" if rand_rdy else "",
        ],
        pythonpaths=setup_flow["pythonpaths"],
    )
    workflow.run()


@pytest.mark.parametrize("DATA_W", [8])
@pytest.mark.parametrize("DEPTH", [4])
@pytest.mark.parametrize("rand_ce", [True])
@pytest.mark.parametrize("rand_rdy", [True])
@pytest.mark.gui
def test_skid_buffer_gui_tb(
    setup_flow, DATA_W: int, DEPTH: int, rand_ce: bool, rand_rdy: bool
):
    """
    Simulate skid_buffer for all elaborated permutations specified.
    Opens gtkwave on completion.
    """
    workflow = HdlWorkflow(
        eda_tool="nvc",
        top="skid_buffer",
        compile_order=setup_flow["compile_order"],
        path_to_working_directory=setup_flow["pwd"],
        generics=[f"{DATA_W=}", f"{DEPTH=}"],
        cocotb="skid_buffer_tb",
        pythonpaths=setup_flow["pythonpaths"],
        plusargs=[
            "rand_ce" if rand_ce else "",
            "rand_rdy" if rand_rdy else "",
        ],
        gui=True,
        waveform_view_file="nvc/skid_bufferDATA_W=8DEPTH=4.gtkw",
    )
    os.environ["COCOTB_RANDOM_SEED"] = str(0xCAFEBABE)
    workflow.run()
