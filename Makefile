
build :
	docker build -t epe-demo .

bash:
	docker run --rm -t \
	--volume `pwd`:/home/demo/epe-demo \
	-i epe-demo bash

base-demo:
	docker run -u root --name epebasedemo --rm -it \
	--volume `pwd`:/mnt \
	-p 179:179 \
	-p 5000:5000 \
	-a stdin \
	-a stdout epe-demo bash

impt-prefix-demo:
	docker run -u root --name epebasedemo --rm -it \
	--volume `pwd`:/mnt \
	-p 179:179 \
	-p 5000:5000 \
	-a stdin \
	-a stdout epe-demo bash

vimpt-prefix-demo:
	docker run -u root --name epebasedemo --rm -it \
	--volume `pwd`:/mnt \
	-p 179:179 \
	-p 5000:5000 \
	-a stdin \
	-a stdout epe-demo bash
