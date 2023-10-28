#!/bin/bash

# Install jq
sudo apt-get install jq

# Create development environment with conda

echo -n "Creating the \`nameko-devex\` environment"
echo -n "To activate this environment, use: conda activate nameko-devex"
conda env create -f environment_dev.yml

# Note:
#
# To activate this environment, use
#
#     $ conda activate nameko-devex
#
# To deactivate an active environment, use
#
#     $ conda deactivate

echo -n "Creating backings and docker containers..."
./dev_run_backingsvcs.sh

echo -n "Start the gateway, orders and products services"
./dev_run.sh gateway.service orders.service products.service &

echo -n "Simple tests, to know if everything was setup correctly"
./test/nex-smoketest.sh local
