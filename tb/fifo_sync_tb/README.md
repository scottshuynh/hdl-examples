# Requirements
* [Python](https://www.python.org/) [>= 3.10](https://www.python.org/downloads/release/python-31018/)
* [hdldepends](https://github.com/pevhall/hdldepends)
* [hdlworkflow](https://github.com/scottshuynh/hdlworkflow)
* [cocotb](https://docs.cocotb.org/en/development/index.html)
* [pytest](https://docs.pytest.org/en/stable/)
* [nvc](https://github.com/nickg/nvc)

# How to run testbench
After installing requirements, run the command:
```sh
./fifo_sync_tb.sh
```
# Running pytest testbench
Utilise pytest to parametrize the DUT generics by generating eight random values for `DATA_W` and `DEPTH`. pytest will simulate the DUT with every permutation of the set of generics that were randomly generated. From this directory, simply run:
```sh
pytest
```