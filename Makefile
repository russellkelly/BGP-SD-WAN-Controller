
build :
		docker build -t epe-demo .

bash:
		docker run --rm -t \
		--volume `pwd`:/root/demo \
		-i epe-demo bash

demo:
		docker run --rm -t \
		--volume `pwd`:/root/demo \
		-p 179:179 \
		-i epe-demo bash
