demo:	base-container demo-container


build :
	docker build -t epe-demo .


base-container:
	python RenderASBRConfigs.py
	docker network create --driver=bridge --subnet=192.168.0.0/16 epe-net
	docker run -d -it --network=epe-net --ip=192.168.0.2 --dns=8.8.8.8 \
	--volume `pwd`:/home/demo/epe-demo \
	-p 179:179 \
	-p 5000:5000 \
	--name epebasedemo epe-demo
	docker exec -d epebasedemo python epe-demo-base-docker.py

demo-container:
	docker run --name epedemo --rm -t --network=epe-net --ip=192.168.0.3 --dns=8.8.8.8 \
	--volume `pwd`:/home/demo/epe-demo \
        -i epe-demo bash

term:
	docker run --rm -t --network=epe-net --dns=8.8.8.8 \
	--volume `pwd`:/home/demo/epe-demo \
        -i epe-demo bash

clean:
	docker stop epebasedemo
	docker rm epebasedemo
	docker network rm epe-net
