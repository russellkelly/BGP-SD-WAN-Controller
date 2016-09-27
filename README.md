# BGP-SD-WAN-Controller
EPE WAN Controller BGP-LU With Add-Path and SPRING Labels

A Python Based SPRING and BGP Route Controller focused on the EPE use case.

To run the demo install EXABGP (version 4.0.0) along with Python 2.7.

This controller can be run on a VM or a BMS, but in addition is all dockerized and can be run in a container (instructions below)

For details on  EXABGP refer to this link:

https://github.com/Exa-Networks/exabgp

INSTALLATION:

To build your own version of the controller all you need to do is install Docker clone the git repository:

        git clone git@github.com:russellkelly/BGP-SD-WAN-Controller.git

Change the TopologyVariables.yaml file to match the environment.  Note:  The exabgp address, if runnning in a docker container) will not need to be changed as the docker container runs in provate epe-net subnet and the controller (and hence the exabgp process) is given address 192.168.0.2.

Then in the cloned (BGP-SD-WAN-Controller) directory run:

        make demo # This runs build: (Builds the image epe-demo) base-container: & demo-container:

The base container is one that exabgp runs in, and peers with ingress and egress ASBR's.  One can connect to the container if required by running:

        docker attach <container-id>|<container name>

Demo container starts another container in epe-net to run the demo from.

If you need another container (say to run ImportantApplications or VeryImportantApplications run:

        make term
        
Term and demo-container will delete upon exit.  The epebasedemo container will not.  To stop and remove run:

        make clean
        

As mentioned the demo has been dramatically enhanced:

    One major function is now the controller dynamically reads the JSON route updates from the Egress ASBR’s (via exabgp) 
    and records the Service prefixes and advertising peer IP from ALL external peer IP peering points  (with BGP add path) 
    and stores these in a Nested Dictionary format.  {Peer:[{route:addpath-id}, …{N)].  This dictionary is updated real time 
    with additions and removals of service routes from any external peer. It also dynamically learns the EPE labels for each 
    external peer and stores these in in a dictionary.  These values are either “exist, “a value” or “0”.  This allows the 
    controller to determine at a base decision point if the peer is there, along with giving it the EPE label to append to 
    the BGP labeled path
    
    The other major function (the real guts of the demo) is using these service prefixes and EPE labels, along with configured 
    EPE peer priority and will then adding and removing or amending routes accordingly.  The python functions keep track of all 
    these variables, any changes to them realtime.  These nested functions monitor the routes and labels constantly, along with 
    scanning the single YAML configuration file so any changes made in this configuration file will be picked up by the programs 
    and the routes/peers will be updated accordingly.  Again all this is running with BGP add-path so the routes and peers are 
    being monitored per external peering link, not just per ASBR 
    
    The Important Prefixes (applications) and Very Important Prefixes can run in parallel and can show a differentiated policy for 
    certain routes (eg by adding SPRING TE Paths etc), or different ingress peers, on top of the “Base” policy applied to the service 
    prefixes detailed above.   There’s a lot more to it…but I’ve run out of energy typing…take a look at the code on Github:

Below is some details on what each file does:


CONFIGURATION FILES
===================

RuntimeVariables.yaml
---------------------
          VeryImportantApplicationsSRPaths - A above this is the section where
          one defines the path for each Egress ASBR.  This file must identify
          the ASBR by the IP it's setting in it NH advertisement.  In this case
          the loopback.  Now when the NH is identified, the appropriate SR path
          is added to the labeled route being advertised..

          VeryImptApplicationsPrefixes - This is the section where the very
          Important application prefixes are added by the operator.  Each
          prefix on a new line.

          ConfiguredEPEPeerList - This is a section you can amend before
          running the demo, it defines the list of peers used in the demo.  
          Note!! This can be all of the EPE enabled peers, or a subset of them.  
          Add them each in a new line with the format:

          [peeraddress'x']:[IP of EPE Peer]

          ImptApplicationsPrefixes - this is the file where the Important
          application prefixes are added by the operator.  Each prefix on
          a new line.



TopologyVariables.yaml
----------------------

          egress_peering_routers - This is the section where the egress
          router(s) are defined.  This is the router, or routers, that send
          the routes to EXABGP, the routes are family inet (Internet service
            routes) and labeled-unicast (EPE Labels) routes

          ingress_peering_routers - This is the section where the ingress
          router(s) are defined.  These are the routers that receive the BGP
          labeled routes from EXABGP

          exabgp - This is the IP, or VIP, of the EXABGP process.  This would 
          not need to be changed if the controller is running in a Docker container,
          as the controller is running in its own epe-net on the host

          Local_as - The local AS for the EXABGP process.
          
          The external_peering section of this file is used to create the configuration
          for the external routers and is used by the progam RenderASBRConfigs.py.
          The file it creates is EgressASBRs.conf.  Likewise the ingress router section 
          is used to creat the file IngressASBRs.conf



SYSTEM RUNTIME FILES
====================


exabgp-ingress-receiving-peer-conf-addpath.j2
-------------------------------------

      The JINJA2 template to build the exabgp-ingress-receiving-peer.conf file
      for EXABGP to use on startup


exabgp-egress-advertising-peer-conf-addpath.j2
-------------------------------------

      The JINJA2 template to build the exabgp-egress-advertising-peer.conf
      file for EXABGP to use on startup

app.py
------
        Fires up a simple HTTP portal on port 5000 so one can post via the
        EXABGP API.


getlabelsandserviceprefixes-addpath.py
------------------------------
          This is the main script that the createsfiles PeerToLabelMapping,
          ServicePrefixes, PeerToAddPathIDMapping.yml and bgplog.json and 
          then parses the JSON formated messages received by EXABGP which 
          itself is writing the updates to bgplog.json.  It stores the learned 
          labels and the service prefixes in the files above.  It is continually 
          running and updating said files.

ImportantApplications-addpath.py
------------------------
          This python script runs atop of the base
          "epe-controller-base-prefixes.py" script.  This particular script
          reads the file ImptApplicationsPrefixes and advertises these if and
          only if the supernet of the prefixi esist in ServicePrefixes
          (the file getlabelsandserviceprefixes.py creates dynamically from
          the received routes from the peering routers).  it uses a different
          set of prioritized EPE peers the user inputs manually upon starting
          the script.



 epe-controller-base-prefixes-addpath.py
-------------------------------
          This is the base python script that routes to the received service
          prefixes (in the ServicePrefixes file) using the file
          ConfiguredEPEPeerList section section (In the RuntimeVariables file)
          as the prioritized list of EPE peers.

epe-demo-addpath.py
---------------
          This is a base start up file, providing noting more than instructions
          on what the demo is doing, and the ability to start up different parts
          of the demo from user input.  This really provides the menu for
          running the demo and just calls the other python programs/scripts.


routes.sh
---------
          This is the shell script called in the
          exabgp-egress-advertising-peer.conf file.  This script simply writes
          the route updates that EXABGP is receiving and exporting in JSON
          format to the file bgplog.json.  Be sure to make the file executable
          by running:
            sudo chmod +x routes.sh

VeryImportantApplications-addpath.py
----------------------------
          Much like ImportantApplications.pyabove this is a program that can
          run a top of "epe-controller-base-prefixes-addpath.py", again checking
          the VeryImptApplicationsPrefixes section of the RuntimeVariables YAML
          file and advertising them if, and only if, the supernet of the prefixi
          exists in ServicePrefixes (the file getlabelsandserviceprefixes.py
          creates dynamically from the received routes from the peering
          routers).  An important difference here is the ability of the
          script to advertise the subnet within the supernet along with a
          user-provisioned SPRING label stack.  The label stack is configured
          in the section "VeryImportantApplicationsSRPaths" of the
          RuntimeVariables YAML file.  This path is updated depending on what
          egress ASBR EPE label being used.  That is; if and EPE label from
          ASBR1 is being used (due to the priority configured by the user
          when first running VeryImportantApplications.py), then SRPATH1
          will be used.  If the EPE peer being used moves to say ASBR2, then
          the SRPATH2 will be used.  The SRPATHs can be updated on the fly
          in the section "VeryImportantApplicationsSRPaths" of the
          RuntimeVariables YAML file, and the python program will pick up
          the new path.

Running the demo in a container
===============================

Once the git repository has been cloned locally the files RuntimeVariables.yaml and TopologyVariables.yaml are amended with the specific Topology and Runtime information for the new Topology

Now one can run controller:

        make demo
        python epe-demo-addpaths-docker.py

Choose option "1"

To run the overlay Important and Very Important Application  programs, make sure option “1” is running. Now the 
prefixes added for Important and VeryImportant applications in the sections of the RuntimeVariables YAML file: are advertised (depending on whether the service prefix is advertised from the specific peers you’ve chosen for these prefixes (below)

To run important applications simply run: 

        make term
        python  ImportantApplications-addpath.py.

Choose "1" - then choose the Peers available. Program will run.
To run Very important applications make sure the SPRING TE paths are defined in “VeryImportantApplicationsSRPaths” then simply run:

        make term (if a new terminal is required)
        python VeryImportantApplications-addpath.py.

Choose "1" - then choose the Peers available. Program will run.


Running the demo in a VM or a BMS
===============================

Build an Ubuntu BMS, or VM and add all requirements per the Dockerfile (detailed below - one can use the Makefile):

        Base ubuntu 14.04 Install
        apt-get update
        apt-get install -qy --no-install-recommends wget python git
        apt-get install -qy openssh-server
        apt-get install -qy openssh-client
        apt-get install -qy python-pip
        apt-get install -qy python-dev
        apt-get install -qy libxml2-dev
        apt-get install -qy libxslt-dev
        apt-get install -qy libssl-dev
        apt-get install -qy libffi-dev
        apt-get install -qy sudo
        apt-get install -qy vim
        apt-get install -qy telnet
        apt-get clean
        pip install flask
        pip install git+https://github.com/Juniper/py-junos-eznc.git
        
        mkdir /home/demo/epe-demo
        
        git clone https://github.com/Exa-Networks/exabgp.git
        /home/demo/epe-demo/exabgp
        git checkout master
        chmod +x setup.py
        sudo ./setup.py install
        cd /home/demo/epe-demo
        cp exabgp.env /usr/local/etc/exabgp/exabgp.env
        
        useradd -m demo && echo "demo:demo" | chpasswd && adduser demo sudo

Once the git repository has been cloned locally the files RuntimeVariables.yaml and TopologyVariables.yaml are amended with the specific Topology and Runtime information for the new Topology

Now one can run controller:

        python epe-demo-addpaths.py

Choose option "1"

To run the overlay Important and Very Important Application  programs, make sure option “1” is running. Now the 
prefixes added for Important and VeryImportant applications in the sections of the RuntimeVariables YAML file: are advertised (depending on whether the service prefix is advertised from the specific peers you’ve chosen for these prefixes (below)

To run important applications simply run the following in a new terminal window: 

        python  ImportantApplications-addpath.py.

Choose "1" - then choose the Peers available. Program will run.

To run Very important applications make sure the SPRING TE paths are defined in “VeryImportantApplicationsSRPaths” then simply run the following in a new terminal window:

        python VeryImportantApplications-addpath.py.

Choose "1" - then choose the Peers available. Program will run.
