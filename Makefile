ifeq ($(OS),Windows_NT)
    PYTHON = python
else
    PYTHON = python3
endif

.PHONY: all build clean info linux-build windows-build

all: build

build:
	$(PYTHON) setup.py build

clean:
	$(PYTHON) setup.py clean

install:
	$(PYTHON) -m pip install -r requirements.txt

info:
	@$(PYTHON) -c "import platform; print(f'OS: {platform.system()} {platform.release()}')"

linux-build:
	@echo "Building for Linux..."
	$(PYTHON) setup.py build

windows-build:
	@echo "Building for Windows..."
	$(PYTHON) setup.py build