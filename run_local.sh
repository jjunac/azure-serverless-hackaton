#!/bin/bash

set -e

source .venv/bin/activate
pip install -r requirements.txt
func start
