test: redis
	@coverage run --branch `which nosetests` -vv --with-yanc -s tests/
	@coverage report -m --fail-under=90

coverage-html: test
	@coverage html -d cover
	@open cover/index.html

tox:
	@PATH=$$PATH:~/.pythonbrew/pythons/Python-2.6.*/bin/:~/.pythonbrew/pythons/Python-2.7.*/bin/:~/.pythonbrew/pythons/Python-3.0.*/bin/:~/.pythonbrew/pythons/Python-3.1.*/bin/:~/.pythonbrew/pythons/Python-3.2.3/bin/:~/.pythonbrew/pythons/Python-3.3.0/bin/ tox

setup:
	@pip install -U -e .\[tests\]

kill_redis:
	-redis-cli -p 7575 shutdown

redis: kill_redis
	redis-server ./redis.conf; sleep 1
	redis-cli -p 7575 info > /dev/null
