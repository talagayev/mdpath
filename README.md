mdpath
==============================
[//]: # (Badges)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI-CD](https://github.com/NDoering99/mdpath/actions/workflows/CI_CD.yml/badge.svg)](https://github.com/NDoering99/mdpath/actions/workflows/CI_CD.yml)
[![codecov](https://codecov.io/gh/NDoering99/mdpath/graph/badge.svg?token=32D80PZOZV)](https://codecov.io/gh/NDoering99/mdpath)
[![Documentation Status](https://readthedocs.org/projects/mdpath/badge/?version=latest)](https://mdpath.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

MDPath - A tool for calculating allosteric communication pathways in proteins by analyzing the mutual information of residue dihedral angle movements throughout an MD simulation.  

https://mdpath.readthedocs.io

## Instalation

#### Clone this repository

Open a new terminal and clone this repository

    cd ~
    git clone https://github.com/NDoering99/mdpath.git

#### Install the openmmdl package with pip

Now you can easily install the package using pip from the cloned repository 

    cd ./mdpath
    pip install .

All dependencies will be automatically istalled alongside the package.

## Usage

MDPath can easily be accesed from the comandline.
Acces this comand to get an overview of all availible flags:
    
    mdpath -h

### Copyright

Copyright (c) 2024, Niklas Piet Doering and Marvin Taterra


#### Acknowledgements
 
Project based on the 
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.1.
