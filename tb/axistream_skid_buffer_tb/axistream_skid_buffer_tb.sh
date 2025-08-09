#!/usr/bin/env bash
prj_dir=$(git rev-parse --show-toplevel)
hdldepends $prj_dir/hdldepends_config.toml --top-entity axistream_skid_buffer --compile-order-vhdl-lib work:compile_order.txt
hdlworkflow nvc axistream_skid_buffer compile_order.txt -g DATA_W=16 -g BUFFER_DEPTH=1024 --cocotb axistream_skid_buffer_tb