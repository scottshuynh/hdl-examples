--------------------------------------------------------------------------------
-- Buffers upstream AXI-Stream and outputs when downstream is ready.
--
-- Buffer should be sized based on expected upstream burst length and expected
-- downstream ready rate.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.standard_pkg.all;
use work.array_pkg.all;
use work.axistream_pkg.all;

entity axistream_skid_buffer is
  generic (
    DATA_W       : natural;
    BUFFER_DEPTH : natural
  );
  port (
    clk_i                    : in  std_logic;
    rst_i                    : in  std_logic;
    ce_i                     : in  std_logic := '1';
    downstream_rdy_i         : in  std_logic;
    upstream_i               : in  axis_tx_basic_iface_t(tdata(DATA_W - 1 downto 0));
    downstream_o             : out axis_tx_basic_iface_t(tdata(DATA_W - 1 downto 0));
    error_upstream_dropped_o : out std_logic
  );
end entity axistream_skid_buffer;

architecture rtl of axistream_skid_buffer is
  constant LOG2_DEPTH  : natural := ceil_log2(BUFFER_DEPTH);
  constant AXIS_FLAT_W : natural := DATA_W + 2;

  signal full         : std_logic;
  signal empty        : std_logic;
  signal fill_counter : unsigned(LOG2_DEPTH downto 0);

  signal axis_upstream_dropped : std_logic := '0';
  signal axis_upstream_write   : std_logic;
  signal axis_upstream_flat    : std_logic_vector(AXIS_FLAT_W - 1 downto 0);

  signal axis_next_read : std_logic := '0';

  constant SKID_W           : natural                                                := 2;
  signal axis_next_flat     : array_slv_t(0 to SKID_W - 1)(AXIS_FLAT_W - 1 downto 0) := (others => (others => '0'));
  signal axis_next_flat_vld : std_logic_vector(SKID_W - 1 downto 0)                  := (others => '0');
  signal axis_handshake     : std_logic;

begin

  axis_upstream_flat  <= to_flat_slv(upstream_i);
  axis_upstream_write <= upstream_i.tvalid and ce_i;

  -- 1 clock cycle latency FIFO.
  i_fifo : entity work.fifo_sync
    generic map(
      DATA_W => AXIS_FLAT_W,
      DEPTH  => BUFFER_DEPTH
    )
    port map
    (
      clk_i          => clk_i,
      rst_i          => rst_i,
      wr_en_i        => axis_upstream_write,
      wr_data_i      => axis_upstream_flat,
      rd_en_i        => axis_next_read,
      rd_data_o      => axis_next_flat(0),
      rd_data_vld_o  => open,
      full_o         => full,
      empty_o        => empty,
      fill_counter_o => fill_counter
    );

  -- FIFO reads to fill up skid buffer.
  -- Always read on handshakes.
  -- Otherwise check to make sure that the FIFO contains values,
  -- and the current set of "next" values are not already filled.
  p_next : process (all)
  begin
    if (axis_handshake = '1') then
      if( empty = '0') then
        axis_next_read <= '1';
      else
        axis_next_read <= '0';
      end if;
    elsif (empty = '0') then
      if and axis_next_flat_vld then
        axis_next_read <= '0';
      else
        axis_next_read <= '1';
      end if;
    else
      axis_next_read <= '0';
    end if;
  end process;

  -- Skid buffer, topped up on every FIFO read.
  -- Data pushed along the skid buffer on every handshake,
  -- or if the skid buffer is only filled 1/2.
  p_clk : process (clk_i)
  begin
    if rising_edge(clk_i) then
      if (ce_i = '1') then
        if (or axis_next_flat_vld) then
          if (axis_handshake = '1') then
            if (and axis_next_flat_vld) then
              axis_next_flat(1)     <= axis_next_flat(0);
              axis_next_flat_vld(1) <= axis_next_flat_vld(0);
              axis_next_flat_vld(0) <= '0';
            else
              axis_next_flat(1)     <= (others => '0');
              axis_next_flat_vld(1) <= '0';
            end if;
          else
            if (axis_next_flat_vld = "01") then
              axis_next_flat(1)     <= axis_next_flat(0);
              axis_next_flat_vld(1) <= axis_next_flat_vld(0);
              axis_next_flat_vld(0) <= '0';
            end if;
          end if;
        end if;

        if (axis_next_read = '1') then
          axis_next_flat_vld(0) <= '1';
        end if;

        if (full = '1' and upstream_i.tvalid = '1') then
          axis_upstream_dropped <= '1';
        else
          axis_upstream_dropped <= '0';
        end if;

        if (rst_i = '1') then
          axis_next_flat_vld <= (others => '0');
        end if;
      end if;
    end if;
  end process;

  error_upstream_dropped_o <= axis_upstream_dropped;

  -- Arbitrates output based on how full the skid buffer is.
  p_out : process (all)
  begin
    if (axis_next_flat_vld(1) = '1') then
      downstream_o <= to_axis_tx_basic(axis_next_flat(1));
      if (downstream_rdy_i = '1') then
        axis_handshake <= '1';
      else
        axis_handshake <= '0';
      end if;
    elsif (axis_next_flat_vld(0) = '1') then
      downstream_o <= to_axis_tx_basic(axis_next_flat(0));
      if (downstream_rdy_i = '1') then
        axis_handshake <= '1';
      else
        axis_handshake <= '0';
      end if;
    else
      downstream_o   <= to_axis_tx_basic(to_slv(0, AXIS_FLAT_W));
      axis_handshake <= '0';
    end if;
  end process;

end architecture;