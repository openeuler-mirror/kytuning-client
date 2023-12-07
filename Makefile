

all: build 


build:
	script/make_rpm.sh


.PHONY: clean install test retest

clean:
	@rm -vf rpm/*.rpm
	@rm -rvf src/__pycache__
	@rm -rvf src/kytuning/__pycache__


install:
	yum -y install ./rpm/kytuning*.rpm

remove:
	yum -y remove kytuning

test:
	kytuning test/unixbench-test-0.yaml

retest: remove clean build install test
