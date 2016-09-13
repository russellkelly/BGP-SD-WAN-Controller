demo:	build base-container demo-container


build :
	docker build -t epe-demo .


base-container:
	docker run -d -it \
	--volume `pwd`:/home/demo/epe-demo \
	-p 179:179 \
	-p 5000:5000 \
	--name epebasedemo epe-demo
	docker exec -d epebasedemo python epe-demo-base-docker.py

demo-container:
	docker run --name epedemo --rm -t \
	--volume `pwd`:/home/demo/epe-demo \
        -i epe-demo bash

term:
	docker run --rm -t \
	--volume `pwd`:/home/demo/epe-demo \
        -i epe-demo bash

clean:
	docker stop epebasedemo
	docker rm epebasedemo
