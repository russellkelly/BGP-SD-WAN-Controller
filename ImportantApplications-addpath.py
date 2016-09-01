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
	loadlabels()
	inv_labelmap = {v: k for k, v in labelmap.items()}
	PeerToASBRMap = loadPeerToASBRMap()
	ImptApplicationsConfiguredPeerList = loadconfiguredEPEPeers()
	bestroutes = FindActiveServicePrefixes()
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



def add_more_specific_routes():
	# In this program we identify a subset of the active service prefixes for Important Applications (Defined by Subnet) and advertise them to VMX1 only to a set of EPE Peers.  If these peers go down we just fall back to the
	# default EPE routing in the BGP EPE program

	
	#Load the labels, the service routes, peers and ASBR Mappings

	loadlabels()
	inv_labelmap = {v: k for k, v in labelmap.items()}
	PeerToASBRMap = loadPeerToASBRMap()
	ImptApplicationsConfiguredPeerList = loadconfiguredEPEPeers()
	bestroutesold = {}
	bestroutes = FindActiveServicePrefixes()
	controller_ip = GetControllerIP()
	while bestroutes.keys() == []:
		print('\n=========================================================================\n\n'"Man oh man you ain't got nuthing going on no-how..."'\n'"Lets just keep rolling until you sort this out......")
		print('\nStart a Global EPE Peer, Bro.....''\n''Or configure another in the Global Configured Peer List File ........''\nIn "ConfiguredEPEPeerList"\n\n\n=========================================================================\n\n\n')
		loadlabels()
		inv_labelmap = {v: k for k, v in labelmap.items()}
		PeerToASBRMap = loadPeerToASBRMap()
		ImptApplicationsConfiguredPeerList = loadconfiguredEPEPeers()
		bestroutesold = {}
		bestroutes = FindActiveServicePrefixes()
		sleep(5)
	while len(bestroutes) > 0:
		print('\n====================================================================================================\n\n''Here is the pertinent run-time information\n')
		print(bestroutes)
		print(ImptApplicationsConfiguredPeerList)
		print(labelmap)
		print(inv_labelmap)
		print(PeerToASBRMap)
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
					print('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']')
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
					print('announce route ' + str(element[0]) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(element[1])])][0])+' label [' + str(element[1]) + ']')
		elif len(bestrouteslistold) >= len(bestrouteslist):
			print("Removing the following routes no longer Advertised by Egress ASBR's: ")
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					print(str(route) +' ')
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutesold[route])])][0])+' label [800000]''\n')})
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
					print('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']')
		print ('\n===================================================================================================\n\n')
		bestroutesold = copy.deepcopy(bestroutes)
		inv_labelmap_old = {v: k for k, v in labelmap.items()}
		loadlabels()
		inv_labelmap = {v: k for k, v in labelmap.items()}
		PeerToASBRMap = loadPeerToASBRMap()
		bestroutes = FindActiveServicePrefixes()
		sleep(5)
	else:
		sleep(5)
		print('\n===================================================================================================\\n\n			All defined EPE Peers Are Idle.\n			Lets just remove the EPE Routes\n\n')
		for route in bestrouteslistold:
			r = requests.post('http://' + str(controller_ip) + ':5000', files={'command': (None, 'withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_no_peers[str(bestroutesold[route])])][0])+' label [800000]''\n')})
			sleep(.2) # Give the API time to process - avoid the HTTP socket error(Max Retries exceeded with url)
			print('withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]')
		print('\n\n===================================================================================================\\n\n\n')
		sleep(5)
		add_more_specific_routes()


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
	ImptApplicationsPrefixes = RuntimeVariables['ImptApplicationsPrefixes']	
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
	rel_path = "ImptApplicationsPeers"
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
	rel_path = "ImptApplicationsPeers"
	abs_file_path = os.path.join(script_dir, rel_path)
	f = open(abs_file_path,'w') #Clear the file or Create the file if it doesn't exist
	f.close()
	loadconfiguredEPEPeers()
	print ("\n\n			WELCOME TO THE IMPORTANT APPLICATION PART OF THE EPE DEMO.....!!!\n\n")
	sleep(1)
	print ("\n====================================================================================================\n\nHave you started option 3 in the EPE demo program!!!???.............  \n\nIf not, open a new window and run 'python new-epe-demo.py' and select option 3......\n\n====================================================================================================\n\n")
	print ("\nPress 1 to start this Part of the demo.......\n\n")
	print ("\nOr press q (..yes small q) to Quit this program.......\n\n")
	os.system("stty erase '^H'")
	m = raw_input("Make your selection.........:  ")
	if m == "1":
		print ('\n====================================================================================================\n\n	All Right Lets Get the Information for the Two EPE Peers For This Part!!\nNote:  We can take as many peers as there are active! We have just limited to 2 for this test.....\n\n')
		print ('Make Sure you have added your Important Applications specific prefixes to the file:\n''......"ImptApplicationsPrefixes".....!!!\n\n====================================================================================================\n\n')
		pass
	elif m == "q":
		print ("\n\nLater Gators........\n\n\n")
		sleep(1)
		exit(0)
	else:
		print("\n\n\nCome on!!! 1 or q only.......:  \n\n")
		sleep(1)
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
	m=raw_input("\nEnter the IP Address of the Primary Peer for your Important Applications: ")
	UserEnteredInformation[n]=m
	n1="peer_address1"
	m1=raw_input("\nEnter the IP Address of the Secondary Peer for your Important Applications: ")
	UserEnteredInformation[n1]=m1
	script_dir = os.path.dirname(__file__)
	rel_path = "ImptApplicationsPeers"
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

				






				

				

				
		
