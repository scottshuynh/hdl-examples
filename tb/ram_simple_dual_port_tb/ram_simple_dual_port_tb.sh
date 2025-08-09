#!/usr/bin/env bash
prj_dir=$(git rev-parse --show-toplevel)
echo $prj_dir
hdldepends $prj_dir/hdldepends_config.toml --top-entity ram_simple_dual_port --compile-order-vhdl-lib work:compile_order.txt
hdlworkflow nvc ram_simple_dual_port compile_order.txt -g DATA_W=16 -g ADDR_W=12 --cocotb ram_simple_dual_port_tb