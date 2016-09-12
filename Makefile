
build :
	docker build -t epe-demo .


base-demo:
	docker run -u demo -it \
	--volume `pwd`:/home/demo/epe-demo \
	-p 179:179 \
	-p 5000:5000 \
	--name epebasedemo epe-demo
	#docker exec -d epebasedemo python epe-demo-addpaths.py
	#docker --debug exec epebasedemo -it /bin/bash exabgp exabgp-egress-advertising-peer-addpath.conf exabgp-ingress-receiving-peer-addpath.conf

prefix-demo:
	docker run --name epeimptprefixdemo --rm -t \
	--volume `pwd`:/home/demo/epe-demo \
        -i epe-demo bash

clean:
	docker stop epebasedemo
	docker rm epebasedemo
