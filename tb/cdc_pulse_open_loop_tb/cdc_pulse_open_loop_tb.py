import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
import random
import math


async def generate_pulses(dut, dst_src_ratio: float, num_pulses: int):
    pulse_width: int = math.ceil(dst_src_ratio * 1.5)

    for _ in range(num_pulses):
        for _ in range(pulse_width):
            dut.src_pulse_i.value = 1
            await RisingEdge(dut.src_clk_i)

        for _ in range(pulse_width):
            dut.src_pulse_i.value = 0
            await RisingEdge(dut.src_clk_i)


async def verify_pulses(dut, num_pulses: int, timeout: int = 100):
    num_verified_pulses = 0
    timeout_counter = 0
    while num_verified_pulses < num_pulses:
        await FallingEdge(dut.dst_clk_i)
        timeout_counter += 1
        if dut.dst_pulse_o.value:
            timeout_counter = 0
            num_verified_pulses += 1
            await FallingEdge(dut.dst_pulse_o)

        assert timeout_counter < timeout, f"Timeout when verifying {num_verified_pulses}th pulse."

    cocotb.log.info(f"Verified {num_verified_pulses} pulses.")


@cocotb.test()
async def test_cdc_pulse(dut):
    """Source clock is faster than destination clock. Drive pulses in and verify pulses out."""
    src_clk_period = 1.0  # TODO: Randomise this.
    dst_clk_period = 2.5  # TODO: Randomise this.

    cocotb.start_soon(Clock(dut.src_clk_i, src_clk_period, "ns").start())
    cocotb.start_soon(Clock(dut.dst_clk_i, dst_clk_period, "ns").start())

    dut.src_pulse_i.value = 0

    for _ in range(random.randint(1, 27)):
        await RisingEdge(dut.src_clk_i)

    num_pulses = 1024
    drive_task = cocotb.start_soon(generate_pulses(dut, dst_clk_period / src_clk_period, num_pulses))
    verify_task = cocotb.start_soon(verify_pulses(dut, num_pulses))

    while not verify_task.done():
        await RisingEdge(dut.dst_clk_i)
