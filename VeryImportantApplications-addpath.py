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
import subprocess
import signal
import requests
from netaddr import *
import yaml
		


labelmap = {}


def exit_gracefully(signum, frame):
	nexthop_ip = GetNextHopIP()
	loadlabels()
	inv_labelmap = {v: k for k, v in labelmap.items()}
	PeerToASBRMap = loadPeerToASBRMap()
	ImptApplicationsConfiguredPeerList = loadconfiguredEPEPeers()
	bestroutes = FindActiveServicePrefixes()
	VeryImportantApplicationsSRPaths = loadVeryImportantApplicationsSRPaths()
	controller_ip = GetControllerIP()
	# restore the original signal handler as otherwise evil things will happen
	# in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
	signal.signal(signal.SIGINT, original_sigint)
	print('\n========================================================================================\n\n			OK Bye.....Lets just remove the EPE Routes\n\n')
	#v = 0
	for route in bestroutes:
		r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [800000]')})
		sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
		print('withdraw route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [800000]')
		#v += 1	
	print('\n\n========================================================================================\n\n\n')
	sleep(1)
	main()
	# restore the exit gracefully handler here    
	signal.signal(signal.SIGINT, exit_gracefully)



def add_more_specific_routes():
	# In this program we identify a subset of the active service prefixes for Important Applications (Defined by Subnet) and advertise them to VMX1 only to a set of EPE Peers.  If these peers go down we just fall back to the
	# default EPE routing in the BGP EPE program

	
	#Load the labels, the service routes, peers and ASBR Mappings
	
	nexthop_ip = GetNextHopIP()
	nexthop_ip_old = 0
	loadlabels()
	inv_labelmap = {v: k for k, v in labelmap.items()}
	PeerToASBRMap = loadPeerToASBRMap()
	ImptApplicationsConfiguredPeerList = loadconfiguredEPEPeers()
	bestroutesold = {}
	VeryImportantApplicationsSRPathsOld = {}
	bestroutes = FindActiveServicePrefixes()
	controller_ip = GetControllerIP()
	VeryImportantApplicationsSRPaths = loadVeryImportantApplicationsSRPaths()
	while bestroutes.keys() == []:
		print('\n=========================================================================\n\n'"Man oh man you ain't got nuthing going on no-how..."'\n'"Lets just keep rolling until you sort this out......")
		print('\nStart a Global EPE Peer, Bro.....''\n''Or configure another in the Global Configured Peer List File ........''\nIn "ConfiguredEPEPeerList"\n\n\n=========================================================================\n\n\n')
		loadlabels()
		inv_labelmap = {v: k for k, v in labelmap.items()}
		PeerToASBRMap = loadPeerToASBRMap()
		ImptApplicationsConfiguredPeerList = loadconfiguredEPEPeers()
		bestroutesold = {}
		VeryImportantApplicationsSRPathsOld = {}
		bestroutes = FindActiveServicePrefixes()
		sleep(5)
	while len(bestroutes) > 0:
		print('\n====================================================================================================\n\n''Here is the pertinent run-time information\n')
		print(nexthop_ip) # remove - for testing only
		print(nexthop_ip_old) # remove - for testing only
		print(bestroutes)
		print(ImptApplicationsConfiguredPeerList)
		print(labelmap)
		print(VeryImportantApplicationsSRPaths)
		print(VeryImportantApplicationsSRPathsOld)
		print("\nHere are the SR Paths we're using: \n")
		for keys in bestroutes.keys():
			print('For route ' +str(keys) +  ' Using SR Path [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +'] with EPE Label [' + str(bestroutes[keys]) + '] On Egress ASBR '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])+'')
		print('\n====================================================================================================\n\n')
		bestrouteslist = bestroutes.keys()
		bestrouteslistold = bestroutesold.keys()
		print ('\n===================================================================================================\n\n')
		if len(bestrouteslistold) == len(bestrouteslist) and cmp(bestroutes, bestroutesold) == 0 and VeryImportantApplicationsSRPathsOld == VeryImportantApplicationsSRPaths and nexthop_ip == nexthop_ip_old:
			print("No Change in the Route Table\n")
			for keys in bestroutes.keys():
				print("Still using Peer "  + str(inv_labelmap[str(bestroutes[keys])]) +  " On Egress ASBR "+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])+' with label path [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + '] for route ' +str(keys))
		elif len(bestrouteslistold) == 0 and len(bestrouteslist) >= 0:
			print("Advertising the following newly learned routes from Egress ASBR's: ")
			for route in bestrouteslist:
				if route not in bestrouteslistold:
					print(str(route) +' ')		
			for route in bestrouteslist:			
				if route not in bestrouteslistold:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + ']')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('announce route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + ']')
		elif nexthop_ip != nexthop_ip_old and nexthop_ip_old != 0:
			print("Next Hop Changed! Advertising the existing routes with the new nexthop: ")
			for route in bestrouteslist:
				print(str(route) +' ')		
			for route in bestrouteslist:			
				r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + ']')})
				sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
				print('announce route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + ']')
		elif VeryImportantApplicationsSRPathsOld != VeryImportantApplicationsSRPaths:
			for SRkeys in VeryImportantApplicationsSRPaths.keys():
				if VeryImportantApplicationsSRPaths[SRkeys] == VeryImportantApplicationsSRPathsOld[SRkeys]:
					pass
				elif VeryImportantApplicationsSRPaths[SRkeys] != VeryImportantApplicationsSRPathsOld[SRkeys] and SRkeys == str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0]):
					print("Advertising all current Very Important Applications' routes with new SR Path For EPE's ASBR"'\n')
					print("Current Prefixes Are: ")
					for route in bestrouteslist:
						print(str(route) + ' ')
					for route in bestrouteslist:
						r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + ']')})
						sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
						print('announce route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + ']')				
		elif len(bestrouteslistold) == len(bestrouteslist) and sum({k:int(v) for k, v in bestroutes.iteritems()}.values()) > 0 and cmp(bestroutes, bestroutesold) != 0 :
			unmatched_item = set(bestroutes.items()) ^ set(bestroutesold.items())
			print("Updating The Following Routes Advertised by Egress ASBR's: ")
			for element in unmatched_item:
				if element[1] == bestroutes[element[0]]:
					print(str(element[0]) +' ')
			for element in unmatched_item:
				if element[1] == bestroutes[element[0]]:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(element[0]) +' next-hop ' + str(nexthop_ip) + ' label ['+ str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(element[1])])][0])])+ ' ' + str(element[1]) + ']')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('announce route ' + str(element[0]) +' next-hop ' + str(nexthop_ip) + ' label ['+ str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(element[1])])][0])])+ ' ' + str(element[1]) + ']')
		elif len(bestrouteslistold) >= len(bestrouteslist):
			print("Removing the following routes no longer Advertised by Egress ASBR's: ")
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					print(str(route) +' ')
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [800000]''\n')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('withdraw route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [800000]')
		elif len(bestrouteslistold) <= len(bestrouteslist):
			print("Advertising the following newly learned routes from Egress ASBR's: ")
			for route in bestrouteslist:
				if route not in bestrouteslistold:
					print(str(route) +' ')
			for route in bestrouteslist:					
				if route not in bestrouteslistold:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'announce route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + ']')})
					sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
					print('announce route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [' + str(VeryImportantApplicationsSRPaths[str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[keys])])][0])]) +' ' + str(bestroutes[keys]) + ']')
		print ('\n===================================================================================================\n\n')
		VeryImportantApplicationsSRPathsOld = copy.deepcopy(VeryImportantApplicationsSRPaths)
		VeryImportantApplicationsSRPaths = loadVeryImportantApplicationsSRPaths()
		nexthop_ip_old = nexthop_ip
		nexthop_ip = GetNextHopIP()
		loadlabels()
		inv_labelmap = {v: k for k, v in labelmap.items()}
		PeerToASBRMap = loadPeerToASBRMap()
		bestroutesold = copy.deepcopy(bestroutes)
		bestroutes = FindActiveServicePrefixes()
		sleep(5)
	else:
		sleep(5)
		print('\n===================================================================================================\\n\n			All defined EPE Peers Are Idle.\n			Lets just remove the EPE Routes\n\n')
		for route in bestrouteslistold:
			r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [800000]''\n')})
			sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
			print('withdraw route ' + str(route) +' next-hop ' + str(nexthop_ip) + ' label [800000]')
		print('\n\n===================================================================================================\\n\n\n')
		sleep(5)
		add_more_specific_routes()


# Get the controller IP from the TopologyVariable YAML File

def GetControllerIP():
	script_dir = os.path.dirname(__file__)
	rel_path = "TopologyVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	file=open(abs_file_path)
	topo_vars = yaml.load(file.read())
	file.close()
	controller_ip = topo_vars['exabgp']['ip_address']
	return controller_ip


def GetNextHopIP():
	script_dir = os.path.dirname(__file__)
	rel_path = "RuntimeVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	file=open(abs_file_path)
	topo_vars = yaml.load(file.read())
	file.close()
	nexthop_ip = topo_vars['VeryImportantApplicationsNextHop']['ip_address']
	return nexthop_ip


# Get the SR TE Path from the RuntimeVariables YAML File

def loadVeryImportantApplicationsSRPaths():
	VeryImportantApplicationsSRPaths = {}
	script_dir = os.path.dirname(__file__)
	rel_path = "RuntimeVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	f = open(abs_file_path,'r')
	RuntimeVariables = yaml.load(f.read())
	VeryImportantApplicationsSRPaths = copy.deepcopy(RuntimeVariables['VeryImportantApplicationsSRPaths'])
	f.close()
	return VeryImportantApplicationsSRPaths



# Find the routes in Important Applications file that are actually active in a service prefix supernet
	
def FindActiveServicePrefixes():
	activeroutes = {}
	ActiveImptApplicationsPrefixes = []
	loadlabels()
	ImptApplicationsConfiguredPeerList = loadconfiguredEPEPeers()
	bestroutes = GetBestRoutes(ImptApplicationsConfiguredPeerList,labelmap)
	servicerouteslist = bestroutes.keys()
	script_dir = os.path.dirname(__file__)
	rel_path = "RuntimeVariables.yaml"
	abs_file_path = os.path.join(script_dir, rel_path)
	f = open(abs_file_path,'r')
	RuntimeVariables = yaml.load(f.read())
	ImptApplicationsPrefixes = RuntimeVariables['VeryImptApplicationsPrefixes']	
	ImptApplicationsIPSet = IPSet(ImptApplicationsPrefixes)
	ImptApplicationsIPNetwork = list(ImptApplicationsIPSet.iter_cidrs())
	serviceIPSet = IPSet(servicerouteslist)
	serviceIPNetwork = list(serviceIPSet.iter_cidrs())
	# Result Stored in 	ActiveimportantPrefixes
	v = 0	
	for line in ImptApplicationsIPNetwork:
		if ImptApplicationsIPNetwork[v] in serviceIPSet:
			ActiveImptApplicationsPrefixes.append(str(ImptApplicationsIPNetwork[v]))
		else:	
			pass
		v +=1
	for key in bestroutes.keys():	
		for line in ActiveImptApplicationsPrefixes:
			if IPNetwork(line) in IPNetwork(key):
				activeroutes[line] = bestroutes[key]
			else:
				continue		
	return activeroutes


def GetBestRoutes(ConfiguredPeerList,labelmap):
	bestroutes = {}
	activepeers = []
	serviceroutes = ReturnActiveServiceRoutes()
	for member in serviceroutes.keys():
		if serviceroutes[str(member)] != {}:
			activepeers.append(member)
	for i in range(0,len(ConfiguredPeerList.keys())):
		if ConfiguredPeerList['peer_address'+ str(i)] in activepeers:
			for j in serviceroutes[ConfiguredPeerList['peer_address'+ str(i)]]:
				if j not in bestroutes.keys():
					bestroutes[j] = labelmap[ConfiguredPeerList['peer_address'+ str(i)]]
				else:
					continue
	return bestroutes

def ReturnActiveServiceRoutes():
	script_dir = os.path.dirname(__file__)
	rel_path = "PeerToAddPathIDMapping.yml"
	abs_file_path = os.path.join(script_dir, rel_path)
	f = open(abs_file_path,'r')
	PeerToAddPathIDMapping = yaml.load(f.read())
	ActiveServiceRoutes = copy.deepcopy(PeerToAddPathIDMapping)
	f.close()
	return ActiveServiceRoutes



def loadconfiguredEPEPeers():
	ImptApplicationsConfiguredPeerList = {}
	script_dir = os.path.dirname(__file__)
	rel_path = "VeryImptApplicationsPeers"
	abs_file_path = os.path.join(script_dir, rel_path)
	f = open(abs_file_path,'r')
	for line in f:
		x = line.split(":")
		a = x[0]
		b = x[1]
		c = len(b)-1
		b = b[0:c]
		ImptApplicationsConfiguredPeerList[a] = b
	f.close()
	return ImptApplicationsConfiguredPeerList
	
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
		add_more_specific_routes()
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


def main():
	UserEnteredInformation = {}
	script_dir = os.path.dirname(__file__)
	rel_path = "VeryImptApplicationsPeers"
	abs_file_path = os.path.join(script_dir, rel_path)
	f = open(abs_file_path,'w') #Clear the file or Create the file if it doesn't exist
	f.close()
	loadconfiguredEPEPeers()
	CurrentIValue = 0
	print ("\n\n			WELCOME TO THE VERY IMPORTANT APPLICATION PART OF THE EPE DEMO.....!!!\n\n")
	sleep(1)
	print ("\n====================================================================================================\n\nHave you started option 3 in the EPE demo program!!!???.............  \n\nIf not, open a new window and run 'python epe-demo-addpaths.py' and select option 4......\n\n====================================================================================================\n\n")
	print ("\nPress 1 to start this Part of the demo.......\n\n")
	print ("\nOr press q (..yes small q) to Quit this program.......\n\n")
	os.system("stty erase '^H'")
	m = raw_input("Make your selection.........:  ")
	if m == "1":
		print ('\n====================================================================================================\n\n	All Right Lets Get the Information for the Two EPE Peers For This Part!!\n\nNote:  We can take as many peers as there are active! We have just limited to 2 for this test.....\n')
		print ('Make Sure you have added your Very Important Applications prefixes to the YAML fileRuntimeVariables\nSection:''......"VeryImptApplicationsPrefixes".....!!!\n\n====================================================================================================\n\n')
		pass
	elif m == "q":
		print ("\n\nLater Gators........\n\n\n")
		sleep(1)
		exit(0)
	else:
		print("\n\n\nCome on!!! 1 or q only.......:  \n\n")
		sleep(0.5)
		main()
	script_dir = os.path.dirname(__file__)
	rel_path = "PeerToASBRMapping"
	abs_file_path = os.path.join(script_dir, rel_path)
	g=open(abs_file_path, "r")
	PeerToASBRMap = {}
	for line in g:
		x = line.split(":")
		a = x[0]
		b = x[1]
		d = len(a)-3
		a = a[0:d]
		c = len(b)-1
		b = b[0:c]
		try:
			PeerToASBRMap[a].append(b)
		except KeyError:
			PeerToASBRMap[a] = [b]
	g.close()	
	print("Your choice of Active EPE Enabled External Peers are:......\n")
	print(str(PeerToASBRMap.keys()))
	os.system("stty erase '^H'")
	n="peer_address0"
	m=raw_input("\nEnter the IP Address of the Primary Peer for your VERY Important Applications: ")
	UserEnteredInformation[n]=m
	n1="peer_address1"
	m1=raw_input("\nEnter the IP Address of the Secondary Peer for your VERY Important Applications: ")
	UserEnteredInformation[n1]=m1
	script_dir = os.path.dirname(__file__)
	rel_path = "VeryImptApplicationsPeers"
	abs_file_path = os.path.join(script_dir, rel_path)
	with open(abs_file_path, 'w') as f:
		for key, value in UserEnteredInformation.items():
			f.write('%s:%s\n' % (key, value))
	f.close()
	sleep(2)
	print ('\n===========================================================================\n\n		All Right Lets Rock & Roll!!\n\n	PRESS CTRL+C TO RETURN TO THIS MENU AT ANY TIME\n\n===========================================================================\n\n')
	print("starting........")
	add_more_specific_routes()
	


if __name__ == "__main__":
	original_sigint = signal.getsignal(signal.SIGINT)
	signal.signal(signal.SIGINT, exit_gracefully)
	main()

				






				

				

				
		
