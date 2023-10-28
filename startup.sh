#!/bin/bash

DEBUG=1 ./dev_run.sh gateway.service orders.service products.service &
./test/nex-smoketest.sh local
