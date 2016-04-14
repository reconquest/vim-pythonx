#!/bin/bash

PYTHONPATH=$(dirname "$0")/pythonx:$(dirname "$0")/tests python2 \
    -m unittest discover -s pythonx/
