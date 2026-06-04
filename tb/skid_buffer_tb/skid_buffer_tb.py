import asyncio
import cocotb
import random
from cocotb.clock import Clock
from cocotb.handle import Immediate
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, with_timeout


async def initialise(dut):
    dut.rst_i.set(Immediate(0))
    dut.ce_i.set(Immediate(1))
    dut.src_data_i.set(Immediate(0))
    dut.src_vld_i.set(Immediate(0))
    dut.dst_rdy_i.set(Immediate(0))
    await RisingEdge(dut.clk_i)


async def reset(dut, num_cycles):
    dut.rst_i.value = 1
    dut.ce_i.value = 1
    dut.src_data_i.value = 0
    dut.src_vld_i.value = 0
    dut.dst_rdy_i.value = 0
    await ClockCycles(dut.clk_i, num_cycles, RisingEdge)
    dut.rst_i.value = 0


async def drive_inputs(dut, inputs):
    num_driven = 0
    try:
        while num_driven < len(inputs):
            dut.src_data_i.value = inputs[num_driven]
            dut.src_vld_i.value = 1
            await RisingEdge(dut.clk_i)

            while True:
                if not dut.ce_i.value.resolve("zeros"):
                    await dut.ce_i.value_change
                    await RisingEdge(dut.clk_i)
                if dut.src_rdy_o.value.resolve("zeros"):
                    break
                await RisingEdge(dut.clk_i)

            num_driven += 1

    except asyncio.CancelledError:
        dut.src_vld_i.value = 0
        cocotb.log.warning(f"Drove {num_driven} inputs before cancelling")
        raise asyncio.CancelledError


async def verify_outputs(dut, expected_outputs):
    num_verified = 0
    try:
        while num_verified < len(expected_outputs):
            await FallingEdge(dut.clk_i)
            if (
                dut.ce_i.value.resolve("zeros")
                and dut.dst_vld_o.value.resolve("zeros")
                and dut.dst_rdy_i.value.resolve("zeros")
            ):
                assert (
                    expected_outputs[num_verified] == dut.dst_data_o.value.to_unsigned()
                )
                num_verified += 1

        cocotb.log.info(f"Verified all {num_verified} outputs!")

    except asyncio.CancelledError:
        cocotb.log.warning(f"Verified {num_verified} outputs before cancelling")
        raise asyncio.CancelledError


async def drive_ce(dut, is_rand: bool = False):
    try:
        if is_rand:
            while True:
                dut.ce_i.value = random.randint(0, 1)
                await RisingEdge(dut.clk_i)
        else:
            dut.ce_i.value = 1
    except asyncio.CancelledError:
        dut.ce_i.value = 0
        raise asyncio.CancelledError


async def drive_rdy(dut, is_rand: bool = False):
    try:
        if is_rand:
            while True:
                dut.dst_rdy_i.value = random.randint(0, 1)
                await RisingEdge(dut.clk_i)
        else:
            dut.dst_rdy_i.value = 1
    except asyncio.CancelledError:
        dut.dst_rdy_i.value = 0
        raise asyncio.CancelledError


@cocotb.test
async def test_skid_buffer(dut):
    Clock(dut.clk_i, 1, "ns").start()
    await initialise(dut)
    await reset(dut, 10)

    DATA_W = dut.DATA_W.value
    num_test_points = 1024
    inputs = [random.randint(0, 2**DATA_W - 1) for _ in range(num_test_points)]

    cocotb.start_soon(drive_inputs(dut, inputs))
    cocotb.start_soon(drive_ce(dut, bool(cocotb.plusargs.get("rand_ce", False))))
    cocotb.start_soon(drive_rdy(dut, bool(cocotb.plusargs.get("rand_rdy", False))))
    verify_task = cocotb.start_soon(verify_outputs(dut, inputs))

    await with_timeout(verify_task, num_test_points * 16, "ns")
