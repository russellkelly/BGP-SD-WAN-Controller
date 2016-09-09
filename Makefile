
build :
	docker build -t epe-demo .

bash:
	docker run --rm -t \
	--volume `pwd`:/home/demo/epe-demo \
	-i epe-demo bash

demo: configure copy

configure:
	docker run -u root --name epedemo --rm -it \
	--volume `pwd`:/mnt \
	-p 179:179 \
	-p 5000:5000 \
	-a stdin \
	-a stdout epe-demo bash

copy:
	docker cp . epedemo:home/demo/epe-demo
