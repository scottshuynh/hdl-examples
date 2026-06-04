import pytest
import os
import subprocess
from pathlib import Path
from hdlworkflow import HdlWorkflow


@pytest.fixture(scope="module")
def setup_flow():
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        hdldepends_proc = subprocess.run(
            [
                "hdldepends",
                f"{repo_root}/hdldepends_config.toml",
                "--top-entity",
                "ram_simple_dual_port",
                "--compile-order-vhdl-lib",
                "work:compile_order.txt",
            ]
        )
        assert hdldepends_proc.returncode == 0

    except subprocess.CalledProcessError:
        raise subprocess.SubprocessError

    flow_cfg = dict()
    test_working_dir = Path(__file__).parent
    flow_cfg["pwd"] = test_working_dir
    flow_cfg["compile_order"] = test_working_dir / "compile_order.txt"
    flow_cfg["pythonpaths"] = [str(test_working_dir)]
    return flow_cfg


@pytest.mark.parametrize("data_w", range(7, 12))
@pytest.mark.parametrize("addr_w", range(4, 10))
@pytest.mark.parametrize("num_pipeline", range(3))
@pytest.mark.prod
def test_ram_simple_dual_port(setup_flow, data_w, addr_w, num_pipeline, worker_id):
    flow = HdlWorkflow(
        eda_tool="nvc",
        top="ram_simple_dual_port",
        compile_order=setup_flow["compile_order"],
        path_to_working_directory=setup_flow["pwd"] / "artefacts" / worker_id,
        generics=[f"{data_w=}", f"{addr_w=}", f"{num_pipeline=}"],
        cocotb="ram_simple_dual_port_tb",
        pythonpaths=setup_flow["pythonpaths"],
    )
    os.environ["COCOTB_RANDOM_SEED"] = "1337"
    flow.run()


@pytest.mark.parametrize("data_w", [9])
@pytest.mark.parametrize("addr_w", [4])
@pytest.mark.parametrize("num_pipeline", [1])
@pytest.mark.gui
def test_ram_simple_dual_port_gui(setup_flow, data_w, addr_w, num_pipeline, worker_id):
    flow = HdlWorkflow(
        eda_tool="nvc",
        top="ram_simple_dual_port",
        compile_order=setup_flow["compile_order"],
        path_to_working_directory=setup_flow["pwd"] / "artefacts" / worker_id,
        generics=[f"{data_w=}", f"{addr_w=}", f"{num_pipeline=}"],
        cocotb="ram_simple_dual_port_tb",
        pythonpaths=setup_flow["pythonpaths"],
        gui=True,
    )
    os.environ["COCOTB_RANDOM_SEED"] = "42"
    flow.run()
