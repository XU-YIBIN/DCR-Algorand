.PHONY: all compile clean

PYTHON=python3
DCR_SMART_CONTRACT=state_smart_contract

all: compile

compile:
	$(PYTHON) ./assets/$(DCR_SMART_CONTRACT).py > ./assets/$(DCR_SMART_CONTRACT).teal

clean:
	rm ./assets/$(DCR_SMART_CONTRACT).teal
