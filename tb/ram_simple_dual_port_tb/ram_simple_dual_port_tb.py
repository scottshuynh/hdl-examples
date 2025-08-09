import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb.types import LogicArray, Range
from typing import List, Tuple
import math
import random

PERIOD_NS = 1


async def initialise_dut(dut, num_clock_cycles: int):
    dut.wr_ce_i.value = 0
    dut.wr_en_i.value = 0
    dut.wr_addr_i.value = 0
    dut.wr_data_i.value = 0
    dut.rd_ce_i.value = 0
    dut.rd_addr_i.value = 0

    for _ in range(num_clock_cycles):
        await RisingEdge(dut.clk_i)


async def drive_random_writes(dut, num_writes: int) -> List[int]:
    # Write all bytes to RAM.

    assert num_writes > 0, "Number of writes to drive must be greater than 0."

    data_w = dut.DATA_W.value
    byte_w = dut.BYTE_W.value
    wr_en_w = int(math.ceil(data_w / byte_w))
    addr_w = dut.ADDR_W.value

    write_datas = [random.randint(-(2 ** (data_w - 1)), 2 ** (data_w - 1) - 1) for _ in range(num_writes)]
    write_addrs = [i for i in range(len(write_datas))]

    dut.wr_ce_i.value = 1
    for write_addr, write_data in enumerate(write_datas):
        dut.wr_en_i.value = LogicArray(2**wr_en_w - 1, Range(wr_en_w - 1, "downto", 0))
        dut.wr_data_i.value = write_data
        dut.wr_addr_i.value = write_addr
        await RisingEdge(dut.clk_i)

    dut.wr_en_i.value = 0
    await RisingEdge(dut.clk_i)
    dut.wr_ce_i.value = 0
    await RisingEdge(dut.clk_i)

    return tuple([write_datas, write_addrs])


async def read_data(dut, read_addrs: List[int]):
    dut.rd_ce_i.value = 1
    for read_addr in read_addrs:
        dut.rd_addr_i.value = read_addr
        await RisingEdge(dut.clk_i)


async def read_to_verify_write_datas(dut, write_datas: List[int], write_addrs: List[int]):
    rd_latency = dut.RD_LATENCY.value
    cocotb.start_soon(read_data(dut, write_addrs))
    read_count = 0
    while read_count < len(write_datas):
        await FallingEdge(dut.clk_i)
        if dut.rd_data_vld_o.value == 1:
            assert dut.rd_data_o.value.to_signed() == write_datas[read_count]
            read_count += 1


@cocotb.test()
async def test_random_writes_and_reads(dut):
    """Write data into RAM and then verify its readback."""
    cocotb.start_soon(Clock(dut.clk_i, PERIOD_NS, "ns").start())
    await initialise_dut(dut, random.randint(1, 10))

    num_writes = 2**dut.ADDR_W.value
    write_datas, write_addrs = await drive_random_writes(dut, num_writes)
    verify_task = cocotb.start_soon(read_to_verify_write_datas(dut, write_datas, write_addrs))

    while not verify_task.done():
        await RisingEdge(dut.clk_i)
