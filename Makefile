help:
	@echo "Usage:"
	@echo "    make            Prints this help."
	@echo "    make test       Runs the tests."


test:
	coverage run manage.py test
	coverage report
	flake8 .
