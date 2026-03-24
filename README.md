# Python Interface for RailDriver

This is a lightweight Python Interface to the RailDriver DLL files contained within Train Simulator Classic allowing the user to directly interact with
the program through Python.

## Getting Started


Use the `RailDriver` class to access the interface, you need to firstly launch the RailDriver utility alongside the TSClassic program.
Once a simulation has been started a full list of available controls is given by running:

```python
from raildriver_api import RailDriver

_raildriver = RailDriver()
print(controller_list)
```

The value for a control is then returned by calling:

```python
print(_raildriver.get_controller_value("Horn", "current"))
```

where the second argument can be either `"current"`, `"min"` or `"max"`.

To set the value of a control use the analogous set method:

```python
_raildriver.set_controller_value("Horn", 1.0)
```