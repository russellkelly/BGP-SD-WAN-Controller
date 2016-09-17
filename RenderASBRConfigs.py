#!/usr/bin/env python

import socket
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
import socket
from sys import stdout
from time import sleep
from jnpr.junos import Device

def exit_gracefully(signum, frame):
	# restore the original signal handler as otherwise evil things will happen
	# in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
	signal.signal(signal.SIGINT, original_sigint)
	main()
	# restore the exit gracefully handler here    
	signal.signal(signal.SIGINT, exit_gracefully)
	
	

def GetControllerIP():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("gmail.com",80))
	controller_ip = s.getsockname()[0]
	s.close()
	return controller_ip


def RenderRouterConfiguration():
	script_dir = os.path.dirname(__file__)
	rel_path = "TopologyVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	file=open(abs_file_path)
	asbr_vars = yaml.load(file.read())
	asbr_vars['home_directory'] = os.path.dirname(os.path.realpath(__file__))
	asbr_vars['controller_ip'] = GetControllerIP()
	file.close()
	template_open = open("ingress_router_config.j2")
	ingress_template = Template(template_open.read())
	template_output = ingress_template.render(asbr_vars)
	script_dir = os.path.dirname(__file__)
	rel_path = "IngressASBRs.conf"
	abs_file_path = os.path.join(script_dir, rel_path)
	with open(abs_file_path, "wb") as f:
		f.write(template_output)
	f.close()
	file.close()
	script_dir = os.path.dirname(__file__)
	rel_path = "TopologyVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	file=open(abs_file_path)
	asbr_vars = yaml.load(file.read())
	asbr_vars['home_directory'] = os.path.dirname(os.path.realpath(__file__))
	asbr_vars['controller_ip'] = GetControllerIP()
	file.close()
	template_open = open("egress_router_config.j2")
	ingress_template = Template(template_open.read())
	template_output = ingress_template.render(asbr_vars)
	script_dir = os.path.dirname(__file__)
	rel_path = "EgressASBRs.conf"
	abs_file_path = os.path.join(script_dir, rel_path)
	with open(abs_file_path, "wb") as f:
		f.write(template_output)
	f.close()
	file.close()


if __name__ == "__main__":
	# store the original SIGINT handler
	original_sigint = signal.getsignal(signal.SIGINT)
	signal.signal(signal.SIGINT, exit_gracefully)
	RenderRouterConfiguration()


