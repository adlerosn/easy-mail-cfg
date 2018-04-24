all: virtual_env
	. virtual_env/bin/activate; python -m easymailcfg

depends: virtual_env
	. virtual_env/bin/activate; python -m pip install -r requirements.txt --upgrade

virtual_env:
	virtualenv -p python3 virtual_env
	make depends
