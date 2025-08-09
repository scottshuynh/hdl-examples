--------------------------------------------------------------------------------
-- AXI-Stream type definitions, utility functions.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package axistream_pkg is
  type axis_tx_basic_iface_t is record
    tdata  : std_logic_vector;
    tvalid : std_logic;
    tlast  : std_logic;
  end record;

  type axis_tx_iface_t is record
    tdata  : std_logic_vector;
    tvalid : std_logic;
    tstrb  : std_logic_vector;
    tkeep  : std_logic_vector;
    tlast  : std_logic;
    tid    : std_logic_vector;
    tdest  : std_logic_vector;
    tuser  : std_logic_vector;
  end record;

  function to_flat_slv (tx : axis_tx_basic_iface_t) return std_logic_vector;
  function to_axis_tx_basic (flat : std_logic_vector) return axis_tx_basic_iface_t;
end package axistream_pkg;

package body axistream_pkg is
  function to_flat_slv (tx : axis_tx_basic_iface_t) return std_logic_vector is
    constant RESULT_W : natural := tx.tdata'length + 2;
    variable result   : std_logic_vector(RESULT_W-1 downto 0);
  begin
    result(tx.tdata'length-1 downto 0) := tx.tdata;
    result(tx.tdata'length)            := tx.tvalid;
    result(tx.tdata'length+1)          := tx.tlast;
    return result;
  end function;

  function to_axis_tx_basic (flat : std_logic_vector) return axis_tx_basic_iface_t is
    constant TDATA_W : natural := flat'length-2;
    variable result  : axis_tx_basic_iface_t(tdata(TDATA_W-1 downto 0));
  begin
    assert (flat'length >= 3) report "Expected minimum flat bitwidth of 3. Got: " & integer'image(flat'length) severity FAILURE;
    result.tdata  := flat(TDATA_W-1 downto 0);
    result.tvalid := flat(TDATA_W);
    result.tlast  := flat(TDATA_W+1);
    return result;
  end function;
end package body axistream_pkg;