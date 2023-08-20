#!/bin/bash

# Run ping in the background using nohup
nohup python3 main.py &

# Display a message indicating that the ping command is running
echo "Milanobot running in the background."