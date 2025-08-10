#!/usr/bin/env bash
prj_dir=$(git rev-parse --show-toplevel)
echo $prj_dir
hdldepends $prj_dir/hdldepends_config.toml --top-entity cdc_pulse_open_loop --compile-order-vhdl-lib work:compile_order.txt
hdlworkflow nvc cdc_pulse_open_loop compile_order.txt -g REG_INPUT=FALSE -g SRC_CLK_PERIOD=1.0 -g DST_CLK_PERIOD=2.5 --cocotb cdc_pulse_open_loop_tb