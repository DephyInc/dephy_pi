# Dephy Pi

Welcome!

This program will download the latest and greatest version of Dephy's custom
Raspberry Pi image, flash your SD card with it, and then allow you to set up your
desired WiFi network, change the hostname, and change the password.

The image is just a standard Raspbian image with all of the prerequisites needed to
work with Dephy's [flexsea](https://github.com/DephyInc/Actuator-Package) library
pre-installed for you so you can get straight to doing the fun stuff!


## Installing

`dephy_pi` has several prerequisites:

* Python >= 3.8
* Linux (Windows support is coming!)
* Git (only needed if installing from source)

It's also **highly** recommended that you install the package in a virtual environment.
You can create one with:

```bash
mkdir ~/.venvs
python3 -m venv ~/.venvs/dephy_pi_env
```

and to activate it:

```bash
source ~/.venvs/dephy_pi_env/bin/activate
```

### Installing from PyPI

To install with `pip`:

```bash
pip3 install dephy_pi
```

### Installing from Source

You can install the program from source by first cloning the repository and then using
pip:

```bash
git clone https://github.com/DephyInc/Dephy_pi.git
cd Dephy_pi
pip3 install .
```


## Usage

To use the program, first insert the SD card you'd like to flash into your computer.

:warning: The code assumes that the SD card will be connected via a removable drive. As such, built-in SD card readers are not currently supported.

Then, run the program:

```bash
dephy_pi create
```

:notebook: This process can take a while!


TODO: Explain running the tests and installing umockdev
