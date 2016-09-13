#!/usr/bin/env python

import socket
from sys import stdout
from sys import stdin
from time import sleep
from jnpr.junos import Device
from lxml import etree
import re
import os
import copy
import re
import subprocess
import signal
import requests
import os
import yaml

labelmap = {}


def exit_gracefully(signum, frame):
	loadlabels()
	inv_labelmap = {v: k for k, v in labelmap.items()}
	PeerToASBRMap = loadPeerToASBRMap()
	ConfiguredPeerList = ReturnPeerList()
	bestroutes = GetBestRoutes(ConfiguredPeerList,labelmap)
	controller_ip = GetControllerIP()
	loadlabels()
	# restore the original signal handler as otherwise evil things will happen
	# in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
	signal.signal(signal.SIGINT, original_sigint)
	print('\n========================================================================================\n\n			OK Bye.....Lets just remove the EPE Routes\n\n')
	#v = 0
	for route in bestroutes:
		r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [800000]')})
		sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
		print('withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [800000]')
		#v += 1	
	print('\n\n========================================================================================\n\n\n')
	sleep(1)
	main()
	# restore the exit gracefully handler here    
	signal.signal(signal.SIGINT, exit_gracefully)




def check_and_add_route():
	#Load the labels, the service routes, peers and ASBR Mappings
	# global serviceroutes
	# global serviceroutesold
	#i = InitialPeerCheck()
	#CurrentPeer = 0
	loadlabels()
	inv_labelmap = {v: k for k, v in labelmap.items()}
	#loadserviceroutes()
	PeerToASBRMap = loadPeerToASBRMap()
	bestroutesold = {}
	ConfiguredPeerList = ReturnPeerList()
	controller_ip = GetControllerIP()
	bestroutes = GetBestRoutes(ConfiguredPeerList,labelmap)
	while bestroutes.keys() == []:
		print('\n=========================================================================\n\n'"Man oh man you ain't got nuthing going on no-how..."'\n'"Lets just keep rolling until you sort this out......")
		print('\nStart a Global EPE Peer, Bro.....''\n''Or configure another in the Global Configured Peer List File ........''\nIn "ConfiguredEPEPeerList"\n\n\n=========================================================================\n\n\n')
		#i = InitialPeerCheck()
		#CurrentPeer = 0
		loadlabels()
		inv_labelmap = {v: k for k, v in labelmap.items()}
		PeerToASBRMap = loadPeerToASBRMap()
		#loadserviceroutes()
		bestroutesold = {}
		ConfiguredPeerList = ReturnPeerList()
		bestroutes = GetBestRoutes(ConfiguredPeerList,labelmap)
		sleep(5)
	while len(bestroutes.keys()) > 0:
		print('\n====================================================================================================\n\n''Here is the pertinent run-time information\n')
		print(labelmap)
		print(PeerToASBRMap)
		print(bestroutes)
		print(bestroutesold)
		print(ConfiguredPeerList)
		print('\n====================================================================================================\n\n')
		bestrouteslist = bestroutes.keys()
		bestrouteslistold = bestroutesold.keys()
		print ('\n===================================================================================================\n\n')
		if len(bestrouteslistold) == len(bestrouteslist) and cmp(bestroutes, bestroutesold) == 0:
			print("No Change in the Route Table\n")
			for keys in bestroutes.keys():
				print("Still using Peer "  + str(inv_labelmap[str(bestroutes[keys])]) +  " On Egress ASBR "+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])+' with label [' + str(bestroutes[keys]) + '] for route ' +str(keys))
		elif len(bestrouteslistold) == 0 and len(bestrouteslist) >= 0:
			print("Advertising the following newly learned routes from Egress ASBR's: ")
			for route in bestrouteslist:
				if route not in bestrouteslistold:
					print(str(route) +' ')		
			for route in bestrouteslist:			
				if route not in bestrouteslistold:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']''\n')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) +  ']')
		elif len(bestrouteslistold) == len(bestrouteslist) and sum({k:int(v) for k, v in bestroutes.iteritems()}.values()) > 0 and cmp(bestroutes, bestroutesold) != 0 :
			unmatched_item = set(bestroutes.items()) ^ set(bestroutesold.items())
			print("Updating The Following Routes Advertised by Egress ASBR's: ")
			for element in unmatched_item:
				if element[1] == bestroutes[element[0]]:
					print(str(element[0]) +' ')
			for element in unmatched_item:
				if element[1] == bestroutes[element[0]]:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(element[0]) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(element[1])])][0])+' label [' + str(element[1]) + ']''\n')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('announce route ' + str(element[0]) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(element[1])])][0])+' label [' + str(element[1]) +  ']')
		elif len(bestrouteslistold) >= len(bestrouteslist) and sum({k:int(v) for k, v in bestroutes.iteritems()}.values()) > 0 and cmp(bestroutes, bestroutesold) != 0 and len(set(bestroutes.items()) & set(bestroutesold.items())) == 0:
			unmatched_item = set(bestroutes.items()) ^ set(bestroutesold.items())
			print("Removing the following routes no longer Advertised by New Egress ASBR's: ")
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					print(str(route) +' ')
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]''\n')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]')
			print("Advertising the following newly learned routes from New Egress ASBR's: ")
			for route in bestrouteslist:
				print(str(route) +' ')		
			for route in bestrouteslist:			
				r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']''\n')})
				sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
				print('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) +  ']')
		elif len(bestrouteslistold) <= len(bestrouteslist) and sum({k:int(v) for k, v in bestroutes.iteritems()}.values()) > 0 and cmp(bestroutes, bestroutesold) != 0 and len(set(bestroutes.items()) & set(bestroutesold.items())) == 0:
			print("Advertising the following newly learned routes from New Egress ASBR's: ")
			for route in bestrouteslist:
				print(str(route) +' ')		
			for route in bestrouteslist:			
				r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) +  ']''\n')})
				sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
				print('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']')
		elif len(bestrouteslistold) >= len(bestrouteslist):
			print("Removing the following routes no longer Advertised by Egress ASBR's: ")
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					print(str(route) +' ')
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]''\n')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]')
		elif len(bestrouteslistold) <= len(bestrouteslist):
			print("Advertising the following newly learned routes from Egress ASBR's: ")
			for route in bestrouteslist:
				if route not in bestrouteslistold:
					print(str(route) +' ')
			for route in bestrouteslist:					
				if route not in bestrouteslistold:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']''\n')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) +  ']')
		print ('\n===================================================================================================\n\n')
		bestroutesold = copy.deepcopy(bestroutes)
		inv_labelmap_old = {v: k for k, v in labelmap.items()}
		loadlabels()
		inv_labelmap = {v: k for k, v in labelmap.items()}
		PeerToASBRMap = loadPeerToASBRMap()
		#loadserviceroutes()
		ConfiguredPeerList = ReturnPeerList()
		bestroutes = GetBestRoutes(ConfiguredPeerList,labelmap)
		#CurrentPeer = ConfiguredPeerList['peer_address'+ str(i)]
		sleep(5)
	else:
		sleep(5)
		print('\n===================================================================================================\\n\n			All defined EPE Peers Are Idle.\n			Lets just remove the EPE Routes\n\n')
		for route in bestrouteslistold:
			r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]''\n')})
			sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
			print('withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]')
		print('\n\n===================================================================================================\\n\n\n')
		sleep(5)
		check_and_add_route()


# Get the controller IP from the TopologyVariable YAML FIle

def GetControllerIP():
	script_dir = os.path.dirname(__file__)
	rel_path = "TopologyVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	file=open(abs_file_path)
	topo_vars = yaml.load(file.read())
	file.close()
	controller_ip = topo_vars['exabgp']['ip_address']
	return controller_ip

def ReturnPeerList():
	script_dir = os.path.dirname(__file__)
	rel_path = "RuntimeVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	f = open(abs_file_path,'r')
	RuntimeVariables = yaml.load(f.read())
	ConfiguredPeerList = copy.deepcopy(RuntimeVariables['ConfiguredPeerList'])
	f.close()
	return ConfiguredPeerList

	
def loadPeerToASBRMap():
	PeerToASBRMap = {}
	script_dir = os.path.dirname(__file__)
	rel_path = "PeerToASBRMapping"
	abs_file_path = os.path.join(script_dir, rel_path)
	while os.stat(abs_file_path).st_size == 0:
		sleep(2)
	g=open(abs_file_path, "r")
	for line in g:
		x = line.split(":")
		a = x[0]
		d = len(a)-3
		a = a[0:d]
		b = x[1]
		c = len(b)-1
		b = b[0:c]
		try:
			PeerToASBRMap[a].append(b)
		except KeyError:
			PeerToASBRMap[a] = [b]
	g.close()
	return PeerToASBRMap

	
	
def loadlabels():
	script_dir = os.path.dirname(__file__)
	rel_path = "PeerToLabelMapping"
	abs_file_path = os.path.join(script_dir, rel_path)
	f=open(abs_file_path, "r")
	if labelmap == {}:
		f.close()
		sleep(2)
		f=open(abs_file_path, "r")
		for line in f:
			x = line.split(":")
			a = x[0]
			d = len(a)-3
			a = a[0:d]
			b = x[1]
			c = len(b)-2
			b = b[1:c]
			labelmap[a] = b
		f.close()
		check_and_add_route()
	else:
		f=open(abs_file_path, "r")
		for line in f:
			x = line.split(":")
			a = x[0]
			d = len(a)-3
			a = a[0:d]
			b = x[1]
			c = len(b)-2
			b = b[1:c]
			labelmap[a] = b
		f.close()
	

def ReturnActiveServiceRoutes():
	script_dir = os.path.dirname(__file__)
	rel_path = "PeerToAddPathIDMapping.yml"
	abs_file_path = os.path.join(script_dir, rel_path)
	f = open(abs_file_path,'r')
	PeerToAddPathIDMapping = yaml.load(f.read())
	ActiveServiceRoutes = copy.deepcopy(PeerToAddPathIDMapping)
	f.close()
	return ActiveServiceRoutes


def GetBestRoutes(ConfiguredPeerList,labelmap):
	bestroutes = {}
	activepeers = []
	# print(labelmap)
	# print(ConfiguredPeerList)
	serviceroutes = ReturnActiveServiceRoutes()
	# print(serviceroutes)
	for member in serviceroutes.keys():
		if serviceroutes[str(member)] != {}:
			activepeers.append(member)
	# print(activepeers)		
	for i in range(0,len(ConfiguredPeerList.keys())):
		if ConfiguredPeerList['peer_address'+ str(i)] in activepeers:
			for j in serviceroutes[ConfiguredPeerList['peer_address'+ str(i)]]:
				if j not in bestroutes.keys():
					bestroutes[j] = labelmap[ConfiguredPeerList['peer_address'+ str(i)]]
				else:
					continue
	# print(bestroutes)
	return bestroutes

def bgpandimportantapps():
	print ('\n===========================================================================\n\n		All Right Lets Rock & Roll!!\n\n	PRESS CTRL+C TO RETURN TO THIS MENU AT ANY TIME\n\n===========================================================================\n\n')
	print("starting........")
	check_and_add_route()
	
def bgpandveryimportantapps():
	print ('\n===========================================================================\n\n		All Right Lets Rock & Roll!!\n\n	PRESS CTRL+C TO RETURN TO THIS MENU AT ANY TIME\n\n===========================================================================\n\n')
	print("starting........")
	check_and_add_route()

def bgponly():
	print ('\n===========================================================================\n\n		All Right Lets Rock & Roll!!\n\n	PRESS CTRL+C TO RETURN TO THIS MENU AT ANY TIME\n\n===========================================================================\n\n')
	print("starting........")
	check_and_add_route()


	

def main():
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
	sleep(2)
	check_and_add_route()


if __name__ == "__main__":
	original_sigint = signal.getsignal(signal.SIGINT)
	signal.signal(signal.SIGINT, exit_gracefully)
	main()

				