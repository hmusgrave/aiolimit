.PHONY: test

test: .devreq
	pytest

.init:
	python -m pip install --upgrade pip
	touch .init

.req: .init requirements.txt
	python -m pip install --upgrade -r requirements.txt
	touch .req

.devreq: .req requirements.dev.txt
	python -m pip install --upgrade -r requirements.dev.txt
	touch .devreq
