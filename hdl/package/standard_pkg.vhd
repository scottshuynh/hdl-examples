--------------------------------------------------------------------------------
-- Standard utility functions.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package standard_pkg is
  function is_sim return boolean;

  function ceil_divide(n : natural; d : natural) return natural;
  function ceil_log2(num : natural) return natural;

  function is_odd(num : natural) return boolean;
  function is_even(num : natural) return boolean;

  function resize(slv : std_logic_vector; slv_w : natural) return std_logic_vector;
end package;

package body standard_pkg is
  function is_sim return boolean is
  begin
    -- pragma translate_off
    return TRUE;
    -- pragma translate_on
    return FALSE;
  end function;

  function ceil_divide(n : natural; d : natural) return natural is
    variable result : natural;
  begin
    result := (n + d - 1) / d;
    return result;
  end function;

  function ceil_log2(num : natural) return natural is
    variable divide : natural := num;
    variable result : natural;
  begin
    l_divide : while (divide /= 1) loop
      divide := ceil_divide(divide, 2);
      if (divide >= 1) then
        result := result + 1;
      end if;  
    end loop;
    return result;
  end function;

  function is_odd(num : natural) return boolean is
    variable result : boolean := false;
  begin
    if (num mod 2 = 1) then
      result := true;
    end if;
    return result;
  end function;

  function is_even(num : natural) return boolean is
    variable result : boolean := false;
  begin
    if (num mod 2 = 0) then
      result := true;
    end if;
    return result;
  end function;

  function resize(slv : std_logic_vector; slv_w : natural) return std_logic_vector is
    variable result : std_logic_vector(slv_w-1 downto 0);
  begin
    result := std_logic_vector(resize(unsigned(slv), slv_w));
    return result;
  end function;
  
end package body;
