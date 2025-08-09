#!/usr/bin/env bash
prj_dir=$(git rev-parse --show-toplevel)
echo $prj_dir
hdldepends $prj_dir/hdldepends_config.toml --top-entity fifo_sync --compile-order-vhdl-lib work:compile_order.txt
hdlworkflow nvc fifo_sync compile_order.txt -g DATA_W=16 -g DEPTH=4096 --cocotb fifo_sync_tb