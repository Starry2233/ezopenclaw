ifeq ($(OS),Windows_NT)
    PYTHON = python
	PIP = $(PYTHON) -m pip
else
    PYTHON = python3
	PIP = pip
endif

.PHONY: all build clean info

all: info install build

build:
	$(PYTHON) setup.py build

clean:
	$(PYTHON) setup.py clean

install:
	$(PIP) install -r requirements.txt

info:
	@$(PYTHON) -c "import platform; print(f'OS: {platform.system()} {platform.release()}')"
