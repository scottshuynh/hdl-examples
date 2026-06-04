# hdl-examples
Example HDL that I've developed.

## Modules
A list of modules that have been implemented and verified.

* RAM Simple Dual Port
* FIFO Synchronous
* Skid Buffer
* AXI-Stream Skid Buffer
* CDC Pulse Open Loop

## Testbenches
### Requirements
* [Python](https://www.python.org/) [>= 3.10](https://www.python.org/downloads/release/python-31018/)
* [hdldepends](https://github.com/pevhall/hdldepends)
* [hdlworkflow](https://github.com/scottshuynh/hdlworkflow)
* [cocotb](https://docs.cocotb.org/en/development/index.html)
* [avl](https://github.com/projectapheleia/avl)
* [pytest](https://docs.pytest.org/en/stable/)
* [pytest-xdist](https://github.com/pytest-dev/pytest-xdist)

### Setup Virtual Environment
From the top directory of this repo, source the setup virtual environment script to make sure the Python environment is set up as intended:
```sh
source ./setup_venv.sh
```

### Running production tests
From the top directory of this repo, run the following command to run all production tests:
```sh
pytest -m prod
```
