.PHONY: all build check test test-python test-js icons clean

all: test

build:
	python3 scripts/build_extensions.py

check:
	python3 scripts/build_extensions.py --check
	node --check extensions/marea-nocturna/main.js
	node --check extensions/musica-abierta/main.js

test-python: build
	python3 -m unittest discover -s tests -p 'test_*.py' -v

test-js:
	node --test tests/*.test.js

test: check test-python test-js

icons:
	bash scripts/render_icons.sh all

clean:
	rm -f packages/*.zip
