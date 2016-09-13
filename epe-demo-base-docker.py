#!/usr/bin/env python

import socket
from sys import stdout
from time import sleep
from jnpr.junos import Device
from lxml import etree
import re
import os
import signal
import time
from pprint import pprint
import json
import sys
import traceback
import yaml
from jinja2 import Template



def exit_gracefully(signum, frame):
	# restore the original signal handler as otherwise evil things will happen
	# in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
	signal.signal(signal.SIGINT, original_sigint)
	main()
	# restore the exit gracefully handler here    
	signal.signal(signal.SIGINT, exit_gracefully)
	
	
def RenderConfigFiles():
	script_dir = os.path.dirname(__file__)
	rel_path = "TopologyVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	file=open(abs_file_path)
	topo_vars = yaml.load(file.read())
	topo_vars['home_directory'] = os.path.dirname(os.path.realpath(__file__))
	file.close()
	template_open = open("exabgp-ingress-receiving-peer-conf-addpath.j2")
	ingress_template = Template(template_open.read())
	template_output = ingress_template.render(topo_vars)
	script_dir = os.path.dirname(__file__)
	rel_path = "exabgp-ingress-receiving-peer-addpath.conf"
	abs_file_path = os.path.join(script_dir, rel_path)
	with open(abs_file_path, "wb") as f:
		f.write(template_output)
	f.close()
	file.close()
	script_dir = os.path.dirname(__file__)
	rel_path = "TopologyVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	file=open(abs_file_path)
	topo_vars = yaml.load(file.read())
	topo_vars['home_directory'] = os.path.dirname(os.path.realpath(__file__))
	file.close()
	template_open = open("exabgp-egress-advertising-peer-conf-addpath.j2")
	ingress_template = Template(template_open.read())
	template_output = ingress_template.render(topo_vars)
	script_dir = os.path.dirname(__file__)
	rel_path = "exabgp-egress-advertising-peer-addpath.conf"
	abs_file_path = os.path.join(script_dir, rel_path)
	with open(abs_file_path, "wb") as f:
		f.write(template_output)
	f.close()
	file.close()
	
	

def main():
	os.system("pkill -9 exabgp")
	os.system("exabgp exabgp-egress-advertising-peer-addpath.conf exabgp-ingress-receiving-peer-addpath.conf")

	
if __name__ == "__main__":
	# store the original SIGINT handler
	original_sigint = signal.getsignal(signal.SIGINT)
	signal.signal(signal.SIGINT, exit_gracefully)
	RenderConfigFiles()
	main()

sleep(1)

