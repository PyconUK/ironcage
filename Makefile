help:
	@echo "Usage:"
	@echo "    make            Prints this help."
	@echo "    make test       Runs the tests."


test:
	STRIPE_API_KEY_PUBLISHABLE=dummy \
	STRIPE_API_KEY_SECRET=dummy \
	python manage.py test
