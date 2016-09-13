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
	
	

def bgpandimportantapps():
	print ('\n===========================================================================\n\n		All Right Lets Rock & Roll!!\n\n	PRESS CTRL+C TO RETURN TO THIS MENU AT ANY TIME\n\n===========================================================================\n\n')
	os.system("exabgp exabgp-egress-advertising-peer-addpath.conf exabgp-ingress-receiving-peer-addpath.conf")
	
def bgpandveryimportantapps():
	print ('\n===========================================================================\n\n		All Right Lets Rock & Roll!!\n\n	PRESS CTRL+C TO RETURN TO THIS MENU AT ANY TIME\n\n===========================================================================\n\n')
	os.system("exabgp exabgp-egress-advertising-peer-addpath.conf exabgp-ingress-receiving-peer-addpath.conf")

def bgponly():
	print ('\n===========================================================================\n\n		All Right Lets Rock & Roll!!\n\n	PRESS CTRL+C TO RETURN TO THIS MENU AT ANY TIME\n\n===========================================================================\n\n')
	sleep(2)
	os.system("exabgp exabgp-egress-advertising-peer-addpath.conf exabgp-ingress-receiving-peer-addpath.conf")


	

def main():
	os.system("pkill -9 exabgp")

	print ("\n================================================================================================================\n\nPart 1 of the Demo Is to showcase EPE TE. Defining the BGP-LU Label on the route\n\nTraffic From vMX1 & vMX8 is routed to the dynamically learned BGP family inet service prefixes using the dynamically \nlearnt EPE labels via BGP-LU !!The controller updates/removes the service routes and EPE labels and\n updates the egress ESBP NH depending on the EPE peer being used!!\nYou can change the order of these EGRESS ASBR by amending ConfiguredEPEPeerList\n\n================================================================================================================\n")
	
	print ("Press 1 to start Part 1: ")
	
	print ("\n=====================================================================================================================\n\nPart 2 of the Demo Engineers Traffic for specific Important Applications prefixes from Both vmx1 and vmx8\n\nThe Important applications' Prefixes need to be defined in the file --> ImptApplicationsPrefixes\nPress 2 and then go to a new window and run --> python ImportantApplications.py\n\n=====================================================================================================================\n")
	
	print ("Press 2 to start Part 2: \n")
	
	print ("\n=====================================================================================================================\n\nPart 3 of the Demo Engineers Traffic for specific Very Important Applications prefixes from Both vmx1 and vmx8\n\nThe COMPLETE PATH is Programmed (SPRING S-NID Label Path and the EPE BGP label) for the prefixes\nThe Important applications' Prefixes need to be defined in the file --> VeryImptApplicationsPrefixes\nPress 3 and then go to a new window and run --> python VeryImportantApplications.py\n\n=====================================================================================================================\n")
	
	print ("Press 3 to start Part 3: \n")
	print ("\nOr press q (..yes small q) to Quit entire Demo.......\n\n")
	os.system("stty erase '^H'")
	m = raw_input("Make your selection.........:  ")

	
		
	if m == "1":
		bgponly()
		main()
	elif m == "2":
		bgpandimportantapps()
		main()
	elif m == "3":
		bgpandveryimportantapps()
		main()
	elif m == "q":
		print ("\n\nLater Gators........\n\n\n")
		os.system("pkill -9 exabgp")
		os.system("pkill -9 python")
		sleep(1)
		exit(0)
	else:
		print("\n\n\nCome on!!! 1,2,3 or q only.......:  \n\n")
		sleep(1)
		main()


	
if __name__ == "__main__":
	# store the original SIGINT handler
	original_sigint = signal.getsignal(signal.SIGINT)
	signal.signal(signal.SIGINT, exit_gracefully)
	RenderConfigFiles()
	#os.system("python getlabelsandserviceprefixes-addpath.py &")
	main()


	


sleep(1)

