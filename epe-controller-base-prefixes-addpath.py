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
#PeerToASBRMap = {}

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
					stdout.write('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']''\n')
					stdout.flush()
		elif len(bestrouteslistold) == len(bestrouteslist) and sum({k:int(v) for k, v in bestroutes.iteritems()}.values()) > 0 and cmp(bestroutes, bestroutesold) != 0 :
			unmatched_item = set(bestroutes.items()) ^ set(bestroutesold.items())
			print("Updating The Following Routes Advertised by Egress ASBR's: ")
			for element in unmatched_item:
				if element[1] == bestroutes[element[0]]:
					print(str(element[0]) +' ')
			for element in unmatched_item:
				if element[1] == bestroutes[element[0]]:
					stdout.write('announce route ' + str(element[0]) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(element[1])])][0])+' label [' + str(element[1]) + ']''\n')
					stdout.flush()
		elif len(bestrouteslistold) >= len(bestrouteslist) and sum({k:int(v) for k, v in bestroutes.iteritems()}.values()) > 0 and cmp(bestroutes, bestroutesold) != 0 and len(set(bestroutes.items()) & set(bestroutesold.items())) == 0:
			unmatched_item = set(bestroutes.items()) ^ set(bestroutesold.items())
			print("Removing the following routes no longer Advertised by New Egress ASBR's: ")
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					print(str(route) +' ')
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					stdout.write('withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]''\n')
					stdout.flush()	
			print("\nAdvertising the following newly learned routes from New Egress ASBR's: ")
			for route in bestrouteslist:
				print(str(route) +' ')		
			for route in bestrouteslist:			
				stdout.write('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']''\n')
				stdout.flush()
		elif len(bestrouteslistold) <= len(bestrouteslist) and sum({k:int(v) for k, v in bestroutes.iteritems()}.values()) > 0 and cmp(bestroutes, bestroutesold) != 0 and len(set(bestroutes.items()) & set(bestroutesold.items())) == 0:
			print("Advertising the following newly learned routes from New Egress ASBR's: ")
			for route in bestrouteslist:
				print(str(route) +' ')		
			for route in bestrouteslist:			
				stdout.write('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']''\n')
				stdout.flush()
		elif len(bestrouteslistold) >= len(bestrouteslist):
			print("Removing the following routes no longer Advertised by Egress ASBR's: ")
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					print(str(route) +' ')
			for route in bestrouteslistold:
				if route not in bestrouteslist:
					stdout.write('withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]''\n')
					stdout.flush()	
		elif len(bestrouteslistold) <= len(bestrouteslist):
			print("Advertising the following newly learned routes from Egress ASBR's: ")
			for route in bestrouteslist:
				if route not in bestrouteslistold:
					print(str(route) +' ')
			for route in bestrouteslist:					
				if route not in bestrouteslistold:
					stdout.write('announce route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap[str(bestroutes[route])])][0])+' label [' + str(bestroutes[route]) + ']''\n')
					stdout.flush()	
		print ('\n===================================================================================================\n\n')
		stdout.flush()
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
		stdout.write('\n===================================================================================================\\n\n			All defined EPE Peers Are Idle.\n			Lets just remove the EPE Routes\n\n')
		for route in bestrouteslistold:
			try:
				stdout.write('withdraw route ' + str(route) +' next-hop '+ str(PeerToASBRMap[str(inv_labelmap_old[str(bestroutesold[route])])][0])+' label [800000]''\n')
			except KeyError:
				continue
		stdout.write('\n\n===================================================================================================\\n\n\n')
		stdout.flush()
		sleep(5)
		check_and_add_route()


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



def main():
	check_and_add_route()


if __name__ == "__main__":
   main()

				