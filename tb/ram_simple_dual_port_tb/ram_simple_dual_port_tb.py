from dataclasses import dataclass
from itertools import chain
from math import ceil
import random

import avl
import avl.templates
import cocotb
from cocotb.triggers import Combine, FallingEdge, RisingEdge, Timer
from cocotb.types import LogicArray

from z3 import BoolRef


@dataclass
class RamSimpleCfg:
    addr_w: int
    data_w: int
    rd_latency: int


class RamWriteRequest(avl.SequenceItem):
    def __init__(
        self,
        name: str,
        parent: avl.Sequencer | avl.Sequence | avl.Component | None,
        ram_cfg: RamSimpleCfg,
    ) -> None:
        super().__init__(name, parent)
        self.wr_en_i = avl.Logic(
            0, fmt=str, auto_random=False, width=ceil(ram_cfg.data_w / 8)
        )
        self.wr_addr_i = avl.Logic(0, fmt=hex, auto_random=False, width=ram_cfg.addr_w)
        self.wr_data_i = avl.Logic(0, fmt=hex, auto_random=False, width=ram_cfg.data_w)
        self.ram_cfg = ram_cfg

    def randomize(
        self, hard: list[BoolRef] | None = None, soft: list[BoolRef] | None = None
    ) -> None:
        self.wr_en_i.value = random.randint(0, 2**self.wr_en_i.width - 1)
        self.wr_addr_i.value = random.randint(0, 2**self.wr_addr_i.width - 1)
        self.wr_data_i.value = random.randint(0, 2**self.wr_data_i.width - 1)

    def get_masked_wr_data(self, prev_data: LogicArray) -> LogicArray:
        bytes = list()
        prev_ram_data = avl.Logic(prev_data.to_unsigned(), width=len(prev_data))
        for idx, wr_en in zip(range(self.wr_en_i.width), self.wr_en_i):
            rem_elem_w = self.wr_data_i.width - 8 * idx
            if wr_en:
                if rem_elem_w >= 8:
                    bytes.insert(
                        0,
                        LogicArray.from_unsigned(
                            self.wr_data_i[8 * idx : 8 * (idx + 1)], 8
                        ),
                    )
                else:
                    bytes.insert(
                        0,
                        LogicArray.from_unsigned(
                            self.wr_data_i[8 * idx : 8 * idx + rem_elem_w], 8
                        ),
                    )

            else:
                if rem_elem_w >= 8:
                    bytes.insert(
                        0,
                        LogicArray.from_unsigned(
                            prev_ram_data[8 * idx : 8 * (idx + 1)], 8
                        ),
                    )
                else:
                    bytes.insert(
                        0,
                        LogicArray.from_unsigned(
                            prev_ram_data[8 * idx : 8 * idx + rem_elem_w], 8
                        ),
                    )

        return LogicArray(chain(*bytes))


class RamReadRequest(avl.SequenceItem):
    def __init__(
        self,
        name: str,
        parent: avl.Sequencer | avl.Sequence | avl.Component | None,
        ram_cfg: RamSimpleCfg,
    ) -> None:
        super().__init__(name, parent)
        self.rd_en_i = avl.Logic(0, fmt=str, auto_random=False, width=1)
        self.rd_addr_i = avl.Logic(0, fmt=hex, auto_random=False, width=ram_cfg.addr_w)

    def randomize(
        self, hard: list[BoolRef] | None = None, soft: list[BoolRef] | None = None
    ) -> None:
        self.rd_en_i.value = random.randint(0, 1)
        self.rd_addr_i.value = random.randint(0, 2**self.rd_addr_i.width - 1)


class RamReadResult(avl.SequenceItem):
    def __init__(
        self,
        name: str,
        parent: avl.Sequencer | avl.Sequence | avl.Component | None,
        ram_cfg: RamSimpleCfg,
    ) -> None:
        super().__init__(name, parent)
        self.rd_addr_i = avl.Logic(0, fmt=hex, auto_random=False, width=ram_cfg.addr_w)
        self.rd_data_i = avl.Logic(0, fmt=hex, auto_random=False, width=ram_cfg.data_w)


class RamWriteSequence(avl.templates.VanillaSequence):
    def __init__(self, name: str, parent: avl.Component, ram_cfg: RamSimpleCfg) -> None:
        super().__init__(name, parent)
        self.ram_cfg = ram_cfg

    async def body(self):
        for _ in range(self.n_items):
            item = RamWriteRequest("wr_req", self, self.ram_cfg)
            await self.start_item(item)
            item.randomize()
            await self.finish_item(item)


class RamReadSequence(avl.templates.VanillaSequence):
    def __init__(self, name: str, parent: avl.Component, ram_cfg: RamSimpleCfg) -> None:
        super().__init__(name, parent)
        self.ram_cfg = ram_cfg

    async def body(self):
        for _ in range(self.n_items):
            item = RamReadRequest("rd_req", self, self.ram_cfg)
            await self.start_item(item)
            item.randomize()
            await self.finish_item(item)


class RamWriteDriver(avl.templates.VanillaDriver):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)
        self.count = 0
        self.item_export = avl.Port("item_export", self)

    async def reset(self):
        self.hdl.wr_ce_i.value = 0
        self.hdl.wr_en_i.value = 0
        self.hdl.wr_addr_i.value = 0
        self.hdl.wr_data_i.value = 0

    async def clear(self):
        await self.reset()

    async def run_phase(self):
        await self.reset()
        await RisingEdge(self.hdl.clk_i)

        while True:
            item = await self.seq_item_port.blocking_get()

            self.hdl.wr_ce_i.value = 1
            self.hdl.wr_en_i.value = item.wr_en_i.value
            self.hdl.wr_addr_i.value = item.wr_addr_i.value
            self.hdl.wr_data_i.value = item.wr_data_i.value
            self.item_export.write(item)
            await RisingEdge(self.hdl.clk_i)

            item.set_event("done")
            self.count += 1
            cocotb.start_soon(self.clear())

    async def report_phase(self):
        self.info(f"{self.count} write requests driven")


class RamReadDriver(avl.templates.VanillaDriver):
    def __init__(self, name: str, parent: avl.Component) -> None:
        super().__init__(name, parent)
        self.count = 0
        self.item_export = avl.Port("item_export", self)

    async def reset(self):
        self.hdl.rd_en_i.value = 0
        self.hdl.rd_addr_i.value = 0

    async def clear(self):
        await self.reset()

    async def run_phase(self):
        await self.reset()
        await RisingEdge(self.hdl.clk_i)

        while True:
            item = await self.seq_item_port.blocking_get()

            self.hdl.rd_en_i.value = item.rd_en_i.value
            self.hdl.rd_addr_i.value = item.rd_addr_i.value
            self.item_export.write(item)
            await RisingEdge(self.hdl.clk_i)

            item.set_event("done")
            self.count += 1
            cocotb.start_soon(self.clear())

    async def report_phase(self):
        self.info(f"{self.count} Read requests driven")


class RamModel(avl.Model):
    def __init__(self, name: str, parent: avl.Component, ram_cfg: RamSimpleCfg) -> None:
        super().__init__(name, parent)
        self.ram_cfg = ram_cfg
        self.ram = {}
        self.rd_item_port = avl.List()
        self.clk = avl.Factory.get_variable(f"{self.get_full_name()}.clk", None)

    async def run_phase(self):
        read_pipeline = tuple([list() for _ in range(self.ram_cfg.rd_latency)])

        while True:
            await RisingEdge(self.clk)
            writes = []
            reads = []

            # Model read latency. Only export expected read values to scoreboard after
            # rd_latency clock cycles have lapsed
            for idx, delay in enumerate(read_pipeline):
                if idx < self.ram_cfg.rd_latency - 1:
                    if delay:
                        read_pipeline[idx + 1].append(delay.pop(0))
                else:
                    if delay:
                        self.item_export.write(delay.pop(0))

            if len(self.item_port) > 0:
                writes.append(self.item_port.pop(0))
            if len(self.rd_item_port) > 0:
                reads.append(self.rd_item_port.pop(0))

            if not writes and not reads:
                continue

            for item in reads:
                if item.rd_en_i.value:
                    expected = RamReadResult("rd", self, self.ram_cfg)
                    expected.rd_addr_i.value = item.rd_addr_i.value
                    expected.rd_data_i.value = self.ram.get(
                        item.rd_addr_i.value,
                        LogicArray.from_unsigned(0, self.ram_cfg.data_w),
                    )
                    if self.ram_cfg.rd_latency:
                        read_pipeline[0].append(expected)
                    else:
                        self.item_export.write(expected)

            for item in writes:
                self.ram[item.wr_addr_i.value] = item.get_masked_wr_data(
                    self.ram.get(
                        item.wr_addr_i.value,
                        LogicArray.from_unsigned(0, self.ram_cfg.data_w),
                    )
                )


class RamReadMonitor(avl.templates.VanillaMonitor):
    def __init__(self, name: str, parent: avl.Component, ram_cfg: RamSimpleCfg) -> None:
        super().__init__(name, parent)
        self.ram_cfg = ram_cfg

    async def run_phase(self):
        z_rd_addr = list()
        while True:
            await FallingEdge(self.hdl.clk_i)
            if self.hdl.rd_data_vld_o.value.resolve("zeros"):
                if self.ram_cfg.rd_latency:
                    if z_rd_addr:
                        actual = RamReadResult("rd", self, self.ram_cfg)
                        actual.rd_addr_i.value = z_rd_addr[0]
                        actual.rd_data_i.value = self.hdl.rd_data_o.value
                        self.item_export.write(actual)
                else:
                    actual = RamReadResult("rd", self, self.ram_cfg)
                    actual.rd_addr_i.value = self.hdl.rd_addr_i.value
                    actual.rd_data_i.value = self.hdl.rd_data_o.value
                    self.item_export.write(actual)

            if self.ram_cfg.rd_latency:
                z_rd_addr.append(self.hdl.rd_addr_i.value)
                if len(z_rd_addr) > self.ram_cfg.rd_latency:
                    z_rd_addr.pop(0)


class RamScoreboard(avl.templates.VanillaScoreboard):
    async def run_phase(self):
        while True:
            self.before_item = await self.before_port.blocking_pop()
            self.after_item = await self.after_port.blocking_pop()

            result = self.before_item.compare(
                self.after_item, verbose=self.verbose, bidirectional=True
            )

            assert result, (
                f"Scoreboard mismatch:\n"
                f"  expected: \n{self.before_item}\n\n"
                f"  actual:   \n{self.after_item}"
            )

            self.compare_count += 1
            self.before_item = None
            self.after_item = None

    async def report_phase(self):
        self.info(f"{self.compare_count} RAM read transactions verified")


class RamSimpleTestEnv(avl.Env):
    def __init__(self, name: str, parent: avl.Component, ram_cfg: RamSimpleCfg) -> None:
        super().__init__(name, parent)
        self.ram_cfg = ram_cfg
        self.clk = avl.Factory.get_variable(f"{self.get_full_name()}.clk", None)
        self.freq_mHz = avl.Factory.get_variable("env.cfg.clock_freq_mHz", None)

        self.wr_driver = RamWriteDriver("wr_driver", self)
        self.wr_sequencer = avl.templates.VanillaSequencer("wr_sequencer", self)

        self.rd_driver = RamReadDriver("rd_driver", self)
        self.rd_sequencer = avl.templates.VanillaSequencer("rd_sequencer", self)
        self.rd_monitor = RamReadMonitor("rd_monitor", self, ram_cfg)

        self.model = RamModel("model", self, ram_cfg)
        self.sb = RamScoreboard("sb", self)

        # Connections
        self.wr_sequencer.seq_item_export.connect(self.wr_driver.seq_item_port)
        self.wr_driver.item_export.connect(self.model.item_port)

        self.rd_sequencer.seq_item_export.connect(self.rd_driver.seq_item_port)
        self.rd_driver.item_export.connect(self.model.rd_item_port)

        self.model.item_export.connect(self.sb.before_port)
        self.rd_monitor.item_export.connect(self.sb.after_port)

    async def run_phase(self):
        cocotb.start_soon(self.clock(self.clk, self.freq_mHz))
        self.raise_objection()
        wr_seq = RamWriteSequence("wr_seq", self.wr_sequencer, self.ram_cfg)
        rd_seq = RamReadSequence("rd_seq", self.rd_sequencer, self.ram_cfg)
        wr_seq_task = cocotb.start_soon(wr_seq.start())
        rd_seq_task = cocotb.start_soon(rd_seq.start())
        await Combine(wr_seq_task, rd_seq_task)
        await Timer(1000, "ns")
        self.drop_objection()
        self.info("Phase complete.")


@cocotb.test
async def test_ram_simple_dual_port(dut):
    # import debugpy

    # debugpy.listen(("localhost", 5678))
    # cocotb.log.info("Connect to debugpy...")
    # debugpy.wait_for_client()

    hdl_cfg = RamSimpleCfg(
        addr_w=dut.ADDR_W.value,
        data_w=dut.DATA_W.value,
        rd_latency=dut.NUM_PIPELINE.value,
    )
    avl.Factory.set_variable("*.hdl", dut)
    avl.Factory.set_variable("*.clk", dut.clk_i)
    avl.Factory.set_variable("env.cfg.timeout_ns", 1e6)
    avl.Factory.set_variable("*.n_items", 32768)
    avl.Factory.set_variable("env.cfg.clock_freq_mHz", 100)

    e = RamSimpleTestEnv("env", None, hdl_cfg)
    await e.start()
