.PHONY: all build check test icon clean

all: test

build:
	python3 scripts/build_extension.py

check:
	python3 scripts/build_extension.py --check

# Re-render the tracked PNG (requires ImageMagick; no SVG delegate needed).
icon:
	bash scripts/render_icon.sh

# Build first because the tests verify that the checked-in package is current.
test: build
	python3 -m unittest discover -s tests -v

clean:
	rm -f packages/*.zip
