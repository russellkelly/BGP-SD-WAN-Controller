#!/usr/bin/env python


import time
from pprint import pprint
import json
import sys
import yaml
import os
from collections import defaultdict

def follow(thefile):
	thefile.seek(0,2)      # Go to the end of the file
	while True:
		line = thefile.readline()
		if not line:
			time.sleep(0.02)    # Sleep very briefly
			continue
		yield line


		

def main():
	PeerToAddPathIDMappingAnnounce = {}
	PeerToAddPathIDMappingWithdraw = {}
	script_dir = os.path.dirname(__file__)
	rel_path = "PeerToLabelMapping"
	abs_file_path = os.path.join(script_dir, rel_path)
	fl = open(abs_file_path,'w')
	fl.close()
	rel_path = "PeerToASBRMapping"
	abs_file_path = os.path.join(script_dir, rel_path)
	fa = open(abs_file_path,'w')
	fa.close()
	rel_path = "PeerToAddPathIDMapping.yml"
	abs_file_path = os.path.join(script_dir, rel_path)
	fap = open(abs_file_path,'w')
	fap.close()
	rel_path = "bgplog.json"
	abs_file_path = os.path.join(script_dir, rel_path)
	logfile = open(abs_file_path,'w+')
	logfile.close()
	rel_path = "bgplog.json"
	abs_file_path = os.path.join(script_dir, rel_path)
	logfile = open(abs_file_path,'r')        
	logline = follow(logfile)
	for line in logline:
		data = json.loads(line)
		if "neighbor" in line:
			message_update_type_keys = data['neighbor']['message']['update'].keys()
			for update_type in message_update_type_keys:
				ipv4_type_keys = data['neighbor']['message']['update'][update_type].keys()
		else:
			main()
		if "ipv4 unicast" in ipv4_type_keys and "announce" in message_update_type_keys:
			service_prefix_keys = data['neighbor']['message']['update']['announce']['ipv4 unicast'].keys()
			for member in service_prefix_keys:
				announcememberprefixlist = data['neighbor']['message']['update']['announce']['ipv4 unicast'][member]
				prefixlist = [x['nlri'] for x in announcememberprefixlist]

				for prefix in prefixlist:
					peerkey = data['neighbor']['message']['update']['announce']['ipv4 unicast'][member][prefixlist.index(prefix)]['path-information']
					if member not in PeerToAddPathIDMappingAnnounce:
						PeerToAddPathIDMappingAnnounce[member] = {}
					if prefix not in PeerToAddPathIDMappingAnnounce[member]:
						PeerToAddPathIDMappingAnnounce[member][prefix] = 0
					PeerToAddPathIDMappingAnnounce[member][prefix] = peerkey
			rel_path = "PeerToAddPathIDMapping.yml"
			PeerToAddPathIDMapping = os.path.join(script_dir, rel_path)
			with open(PeerToAddPathIDMapping, 'w') as yaml_file:
			 	yaml.safe_dump(PeerToAddPathIDMappingAnnounce, yaml_file, default_flow_style=False, encoding='utf-8', allow_unicode=True)
		elif "ipv4 unicast" in ipv4_type_keys and "withdraw" in message_update_type_keys:
				withdrawmemberprefixlist = data['neighbor']['message']['update']['withdraw']['ipv4 unicast']
				prefixlist = [x['nlri'] for x in withdrawmemberprefixlist]
				for i in range(0,len(prefixlist)):
					prefix = prefixlist[i]
					peerkey = data['neighbor']['message']['update']['withdraw']['ipv4 unicast'][i]['path-information']
					PeerToAddPathIDMappingWithdraw[str(prefix)] = str(peerkey)
					WithdrawPrefix = str(prefix)
					for member in PeerToAddPathIDMappingAnnounce:
						#print(member)
						for prefix in PeerToAddPathIDMappingAnnounce[str(member)].copy():
							for key in PeerToAddPathIDMappingAnnounce[str(member)].keys():
								if key == WithdrawPrefix and PeerToAddPathIDMappingAnnounce[str(member)][str(prefix)] == str(peerkey):
									PeerToAddPathIDMappingAnnounce[str(member)].pop(WithdrawPrefix,None)
									break
								else:
									pass
				rel_path = "PeerToAddPathIDMapping.yml"
				PeerToAddPathIDMapping = os.path.join(script_dir, rel_path)
				with open(PeerToAddPathIDMapping, 'w') as yaml_file:
					yaml.safe_dump(PeerToAddPathIDMappingAnnounce, yaml_file, default_flow_style=False, encoding='utf-8', allow_unicode=True)
		elif "ipv4 nlri-mpls" in ipv4_type_keys and "announce" in message_update_type_keys:
			neighbor_message_update_announce_keys = data["neighbor"]["message"]["update"]["announce"]['ipv4 nlri-mpls'].keys()
			for announce_peer in neighbor_message_update_announce_keys:
				external_peers = data["neighbor"]["message"]["update"]["announce"]['ipv4 nlri-mpls'][announce_peer]
				external_peers_list = [x['nlri'] for x in external_peers]
				rel_path = "PeerToASBRMapping"
				PeerToASBRMapping = os.path.join(script_dir, rel_path)
				for external_peer_ip in external_peers_list:
					if str(external_peer_ip) in open(PeerToASBRMapping).read():
						g = open(PeerToASBRMapping, "r+")
						d = g.readlines()
						g.seek(0)
						for line in d:
							if str(external_peer_ip) not in line:
								g.write(line)
						g.truncate()
						g.close()
						g = open(PeerToASBRMapping,'a')
						g.write(str(external_peer_ip) + ':' + str(announce_peer)+'\n') # python will convert \n to os.linesep
						g.close()
					else:	
						g = open(PeerToASBRMapping,'a')
						g.write(str(external_peer_ip) + ':' + str(announce_peer)+'\n') # python will convert \n to os.linesep
						g.close()	
					peerlabel = data["neighbor"]["message"]["update"]["announce"]['ipv4 nlri-mpls'][announce_peer][external_peers_list.index(external_peer_ip)]['label']
					rel_path = "PeerToLabelMapping"
					PeerToLabelMapping = os.path.join(script_dir, rel_path)
					if str(external_peer_ip) in open(PeerToLabelMapping).read():
						g = open(PeerToLabelMapping, "r+")
						d = g.readlines()
						g.seek(0)
						for line in d:
							if str(external_peer_ip) not in line:
								g.write(line)
						g.truncate()
						g.close()
						g = open(PeerToLabelMapping,'a')
						g.write(str(external_peer_ip) + ':' + str(peerlabel)+'\n') # python will convert \n to os.linesep
						g.close()
					else:	
						g = open(PeerToLabelMapping,'a')
						g.write(str(external_peer_ip) + ':' + str(peerlabel)+'\n') # python will convert \n to os.linesep
						g.close()
		elif "ipv4 nlri-mpls" in ipv4_type_keys and "withdraw" in message_update_type_keys:
			neighbor_message_update_withdraw_keys = data["neighbor"]["message"]["update"]["withdraw"]['ipv4 nlri-mpls']
			for withdraw_peer in neighbor_message_update_withdraw_keys:
				external_peer_withdraws = data["neighbor"]["message"]["update"]["withdraw"]['ipv4 nlri-mpls']
				prefixlist = [x['nlri'] for x in external_peer_withdraws]
				for external_peer_ip in prefixlist:
						label = (data["neighbor"]["message"]["update"]["withdraw"]['ipv4 nlri-mpls'][prefixlist.index(external_peer_ip)]['label'])
						rel_path = "PeerToLabelMapping"
						PeerToLabelMapping = os.path.join(script_dir, rel_path)
						if str(external_peer_ip) in open(PeerToLabelMapping).read():
							f = open(PeerToLabelMapping, "r+")
							d = f.readlines()
							f.seek(0)
							for line in d:
								if str(external_peer_ip) not in line:
									f.write(line)
							f.truncate()
							f.close()
							f = open(PeerToLabelMapping,'a')
							f.write(str(external_peer_ip) + ':' + str(label)+'\n') 
							f.close()
						else:
							f = open(PeerToLabelMapping,'a')
							f.write(str(external_peer_ip) + ':' + str(label)+'\n') # python will convert \n to os.linesep
							f.close()		
						i =+ 1
				i =+ 1
		else:
			pass


if __name__ == "__main__":
    main()


