ifeq ($(OS),Windows_NT)
    PYTHON = python
else
    PYTHON = python3
endif

.PHONY: all build clean info

all: build

build:
	$(PYTHON) setup.py build

clean:
	$(PYTHON) setup.py clean

install:
	$(PYTHON) -m pip install -r requirements.txt

info:
	@$(PYTHON) -c "import platform; print(f'OS: {platform.system()} {platform.release()}')"
