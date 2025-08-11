import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
import random
from typing import List


async def reset_dut(dut, num_clock_cycles: int):
    """Resets DUT for a number of clock cycles.

    Args:
        num_clock_cycles (int): Number of clock cycles to hold DUT in reset.
    """
    dut.rst_i.value = 1
    dut.upstream_i.tdata.value = 0
    dut.upstream_i.tvalid.value = 0
    dut.upstream_i.tlast.value = 0
    dut.downstream_rdy_i.value = 0

    for _ in range(num_clock_cycles):
        await RisingEdge(dut.clk_i)

    dut.rst_i.value = 0
    await RisingEdge(dut.clk_i)


async def drive_axis_upstream(dut, write_datas: List[int]):
    """Drives data into dut every clock cycle.

    Args:
        write_datas (List[int]): List of write data.
    """
    for write_data in write_datas:
        dut.upstream_i.tdata.value = write_data
        dut.upstream_i.tvalid.value = 1
        await RisingEdge(dut.clk_i)

    dut.upstream_i.tvalid.value = 0
    await RisingEdge(dut.clk_i)


async def drive_random_readys(dut, downstream_slow_rate: int):
    """Drives ready high randomly a rate of 1/N.

    ...where N is the integer rate of downstream slower than the system clock.

    Args:
        downstream_slow_rate (int): N
    """
    while True:
        dut.downstream_rdy_i.value = random.randint(1, downstream_slow_rate) == 1
        await RisingEdge(dut.clk_i)


async def verify_axis_downstream(dut, verify_datas: List[int]):
    """Verifies DUT output data on every AXIS handshake.

    Args:
        verify_datas (List[int]): List of data to scoreboard vs DUT.
    """
    verify_count = 0
    timeout_counter = 0
    while verify_count < len(verify_datas):
        await FallingEdge(dut.clk_i)
        assert (
            timeout_counter < 2048
        ), f"Verification idx #{verify_count} timed out! Expecting: {verify_datas[verify_count]}"
        if dut.axis_handshake.value == 1:
            assert (
                verify_datas[verify_count] == dut.downstream_o.tdata.value.to_signed()
            ), f"Expecting: {verify_datas[verify_count]}, got: {dut.downstream_o.tdata.value.to_signed()}"
            verify_count += 1
            timeout_counter = 0

        timeout_counter += 1


@cocotb.test()
async def drive_and_validate_slow_downstream(dut):
    """Drives random data into DUT at full rate. Scoreboard DUT on every AXIS handshake."""
    cocotb.start_soon(Clock(dut.clk_i, 1, "ns").start())
    await reset_dut(dut, random.randint(1, 10))

    num_writes = dut.BUFFER_DEPTH.value
    data_w = dut.DATA_W.value
    write_datas = [random.randint(-(2 ** (data_w - 1)), 2 ** (data_w - 1) - 1) for _ in range(num_writes)]

    write_task = cocotb.start_soon(drive_axis_upstream(dut, write_datas))
    random_ready_task = cocotb.start_soon(drive_random_readys(dut, 4))
    verify_task = cocotb.start_soon(verify_axis_downstream(dut, write_datas))

    cocotb.log.info("Begin scoreboard verification...")
    while not verify_task.done():
        await RisingEdge(dut.clk_i)

    cocotb.log.info("Scoreboard complete!")

    await RisingEdge(dut.clk_i)
    await FallingEdge(dut.clk_i)
    assert (
        dut.downstream_o.tvalid.value == 0
    ), "Skid buffer is not flushed after all buffered data was streamed out of FIFO!"
