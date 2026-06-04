--------------------------------------------------------------------------------
-- Type definitions and utility functions for arrays.
--------------------------------------------------------------------------------

library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

package array_pkg is

  type array_integer_t is array (natural range <>) of integer;

  type array_slv_t is array (natural range <>) of std_logic_vector;

  type array_signed_t is array(natural range <>) of signed;

  type array_unsigned_t is array(natural range <>) of unsigned;

  constant NULL_ARRAY_INTEGER  : array_integer_t(0 to -1)               := (others => 0);
  constant NULL_ARRAY_SLV      : array_slv_t(0 to -1)(-1 downto 0)      := (others => (others => '0'));
  constant NULL_ARRAY_SIGNED   : array_signed_t(0 to -1)(-1 downto 0)   := (others => (others => '0'));
  constant NULL_ARRAY_UNSIGNED : array_unsigned_t(0 to -1)(-1 downto 0) := (others => (others => '0'));
  function zeros (arr_len      : positive; slv_w : positive) return array_slv_t;
  function zeros (arr_len   : positive; num_w : positive) return array_signed_t;
  function zeros (arr_len : positive; num_w : positive) return array_unsigned_t;
  function to_array_signed (arr_int : array_integer_t; num_w : positive) return array_signed_t;

end package array_pkg;

package body array_pkg is

  function zeros (arr_len : positive; slv_w : positive) return array_slv_t is
    constant RESULT : array_slv_t(0 to arr_len - 1)(slv_w - 1 downto 0) := (others => (others => '0'));
  begin
    return RESULT;
  end function zeros;

  function zeros (arr_len : positive; num_w : positive) return array_signed_t is
    constant RESULT : array_signed_t(0 to arr_len - 1)(num_w - 1 downto 0) := (others => (others => '0'));
  begin
    return RESULT;
  end function zeros;

  function zeros (arr_len : positive; num_w : positive) return array_unsigned_t is
    constant RESULT : array_unsigned_t(0 to arr_len - 1)(num_w - 1 downto 0) := (others => (others => '0'));
  begin
    return RESULT;
  end function zeros;

  function to_array_signed (arr_int : array_integer_t; num_w : positive) return array_signed_t is
    variable result : array_signed_t(arr_int'range)(num_w - 1 downto 0);
  begin
    l_elem : for idx in arr_int'range loop

      result(IDX) := to_signed(arr_int(IDX), num_w);

    end loop;

    return result;
  end function to_array_signed;

end package body array_pkg;
