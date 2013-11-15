mongodatabase = holmes

test: drop_test data_test unit integration kill_run

unit:
	@coverage run --branch `which nosetests` -vv --with-yanc -s tests/unit/
	@coverage report -m --fail-under=90

coverage-html: mongo_test unit
	@coverage html -d cover

integration: kill_run run_daemon
	@`which nosetests` -vv --with-yanc -s tests/integration/;EXIT_CODE=$$?;$(MAKE) kill_run;exit $(EXIT_CODE)

tox:
	@PATH=$$PATH:~/.pythonbrew/pythons/Python-2.6.*/bin/:~/.pythonbrew/pythons/Python-2.7.*/bin/:~/.pythonbrew/pythons/Python-3.0.*/bin/:~/.pythonbrew/pythons/Python-3.1.*/bin/:~/.pythonbrew/pythons/Python-3.2.3/bin/:~/.pythonbrew/pythons/Python-3.3.0/bin/ tox

setup:
	@pip install -U -e .\[tests\]

drop_mongo:
	@rm -rf /tmp/$(mongodatabase)/mongodata

kill_mongo:
	@ps aux | awk '(/mongod/ && $$0 !~ /awk/){ system("kill -9 "$$2) }'

mongo: kill_mongo
	@mkdir -p /tmp/$(mongodatabase)/mongodata
	@mongod --dbpath /tmp/$(mongodatabase)/mongodata --logpath /tmp/$(mongodatabase)/mongolog --port 6685 --quiet &
	@sleep 3

kill_mongo_test:
	@ps aux | awk '(/mongod.+test/ && $$0 !~ /awk/){ system("kill -9 "$$2) }'

mongo_test: kill_mongo_test
	@rm -rf /tmp/$(mongodatabase)/mongotestdata && mkdir -p /tmp/$(mongodatabase)/mongotestdata
	@mongod --dbpath /tmp/$(mongodatabase)/mongotestdata --logpath /tmp/$(mongodatabase)/mongotestlog --port 6686 --quiet &
	@sleep 3

drop:
	@-cd holmes/ && alembic downgrade base
	@mysql -u root -e "DROP DATABASE IF EXISTS holmes; CREATE DATABASE IF NOT EXISTS holmes"
	@echo "DB RECREATED"

drop_test:
	@-cd tests/ && alembic downgrade base
	@mysql -u root -e "DROP DATABASE IF EXISTS test_holmes; CREATE DATABASE IF NOT EXISTS test_holmes"
	@echo "DB RECREATED"

data:
	@cd holmes/ && alembic upgrade head

data_test:
	@cd tests/ && alembic upgrade head

migration:
	@cd holmes/ && alembic revision -m "$(DESC)"

kill_run:
	@ps aux | awk '(/.+holmes-api.+/ && $$0 !~ /awk/){ system("kill -9 "$$2) }'

run_daemon:
	@holmes-api -vvv -c ./holmes/config/local.conf &

run:
	@holmes-api -vvv -c ./holmes/config/local.conf

worker:
	@holmes-worker -vvv -c ./holmes/config/local.conf

kill_workers:
	@ps aux | awk '(/.+holmes-worker.+/ && $$0 !~ /awk/){ system("kill -9 "$$2) }'

workers: kill_workers
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
	@holmes-worker -c ./holmes/config/local.conf &
