
build :
		docker build -t epe-demo .

bash:
		docker run --rm -t \
		--volume `pwd`:/home/demo/epe-demo \
		-i epe-demo bash

demo:
		docker run --rm -t \
		--volume `pwd`:/home/demo/epe-demo \
		-p 179:179 \
		-i epe-demo bash
