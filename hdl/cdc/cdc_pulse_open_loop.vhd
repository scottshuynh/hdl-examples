--------------------------------------------------------------------------------
-- Used to send a pulse from source clock domain to destination clock domain.
--
-- If pulse is driven combinatorially, make sure to connect the correct source
-- clock to synchronise to and set `REG_INPUT=1`.
--
-- If the pulse is already synchronous to a clock, set `REG_INPUT=0`.
--
-- Specifying the clock periods of the source and destination clocks is
-- important for clarity. An assert check will be run in simulation to verify
-- the assumption below.
--
-- For synthesis, write a constraint to set the maximum delay of any datapaths
-- from src_clk to dst_clock.
--
-- Assumption: 
-- 1. Pulse must be at least x1.5 the period of the destination clock frequency.
-- 2. Pulse will be sampled by the destination clock at least once and possibly
--    twice.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.standard_pkg.all;

entity cdc_pulse_open_loop is
  generic (
    REG_INPUT      : boolean;
    SRC_CLK_PERIOD : real;
    DST_CLK_PERIOD : real
  );
  port (
    src_clk_i   : in  std_logic;
    dst_clk_i   : in  std_logic;
    src_pulse_i : in  std_logic;
    dst_pulse_o : out std_logic
  );
end entity cdc_pulse_open_loop;

architecture rtl of cdc_pulse_open_loop is
  constant MINIMUM_PULSE_WIDTH : real := DST_CLK_PERIOD * 1.5;
  signal dst_pulse_reg : std_logic_vector(1 downto 0) := (others => '0');
begin

  g_input_reg : if (REG_INPUT) generate
    signal src_pulse_reg : std_logic;
  begin
    g_sim : if (is_sim) generate
      signal src_pulse_counter : real := 0.0;
    begin
      p_verify_assumption : process (src_clk_i)
      begin
        if rising_edge(src_clk_i) then
          if (src_pulse_reg = '1') then
            src_pulse_counter <= src_pulse_counter + SRC_CLK_PERIOD;
          else
            if (src_pulse_counter > 0.0) then
              assert (src_pulse_counter >= MINIMUM_PULSE_WIDTH)
                report "Timing violation: Pulse from src_clk_i must be held high for " &
                real'image(MINIMUM_PULSE_WIDTH) &
                ". Got: " & real'image(src_pulse_counter) & "."
                severity FAILURE;
              src_pulse_counter <= 0.0;
            end if;
          end if;
        end if;
      end process;
    end generate;

    p_src_clk : process (src_clk_i)
    begin
      if rising_edge(src_clk_i) then
        src_pulse_reg <= src_pulse_i;
      end if;
    end process;

    p_dst_clk : process (dst_clk_i)
    begin
      if rising_edge(dst_clk_i) then
        dst_pulse_reg(0) <= src_pulse_reg;
        dst_pulse_reg(1) <= dst_pulse_reg(0);
      end if;
    end process;

    dst_pulse_o <= dst_pulse_reg(1);
  end generate;

  g_no_input_reg : if (not REG_INPUT) generate
  begin
    g_sim : if (is_sim) generate
      signal src_pulse_counter : real := 0.0;
    begin
      p_verify_assumption : process (src_clk_i)
      begin
        if rising_edge(src_clk_i) then
          if (src_pulse_i = '1') then
            src_pulse_counter <= src_pulse_counter + SRC_CLK_PERIOD;
          else
            if (src_pulse_counter > 0.0) then
              assert (src_pulse_counter >= MINIMUM_PULSE_WIDTH)
                report "Timing violation: Pulse from src_clk_i must be held high for " &
                real'image(MINIMUM_PULSE_WIDTH) &
                ". Got: " & real'image(src_pulse_counter) & "."
                severity FAILURE;
              src_pulse_counter <= 0.0;
            end if;
          end if;
        end if;
      end process;
    end generate;

    p_dst_clk : process (dst_clk_i)
    begin
      if rising_edge(dst_clk_i) then
        dst_pulse_reg(0) <= src_pulse_i;
        dst_pulse_reg(1) <= dst_pulse_reg(0);
      end if;
    end process;

    dst_pulse_o <= dst_pulse_reg(1);
  end generate;

end architecture rtl;