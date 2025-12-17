.PHONY: example test coverage translatable_strings update_translations help
.DEFAULT_GOAL := help

example:  ## Run the example application
	python example/manage.py migrate --noinput
	-DJANGO_SUPERUSER_PASSWORD=p python example/manage.py createsuperuser \
		--noinput --username="$(USER)" --email="$(USER)@mailinator.com"
	python example/manage.py runserver

example_async:
	python example/manage.py migrate --noinput
	-DJANGO_SUPERUSER_PASSWORD=p python example/manage.py createsuperuser \
		--noinput --username="$(USER)" --email="$(USER)@mailinator.com"
	daphne example.asgi:application

example_test:  ## Run the test suite for the example application
	python example/manage.py test example

test:  ## Run the test suite
	DJANGO_SETTINGS_MODULE=tests.settings \
		python -m django test $${TEST_ARGS:-tests}

test_selenium:  ## Run frontend tests written with Selenium
	DJANGO_SELENIUM_TESTS=true DJANGO_SETTINGS_MODULE=tests.settings \
		python -m django test $${TEST_ARGS:-tests}

coverage:  ## Run the test suite with coverage enabled
	python --version
	DJANGO_SETTINGS_MODULE=tests.settings \
		python -b -W always -m coverage run -m django test -v2 $${TEST_ARGS:-tests}
	coverage report
	coverage html
	coverage xml

translatable_strings:  ## Update the English '.po' file
	cd debug_toolbar && python -m django makemessages -l en --no-obsolete
	@echo "Please commit changes and run 'tx push -s' (or wait for Transifex to pick them)"

update_translations:  ## Download updated '.po' files from Transifex
	tx pull -a --minimum-perc=10
	cd debug_toolbar && python -m django compilemessages

.PHONY: example/django-debug-toolbar.png
example/django-debug-toolbar.png: example/screenshot.py  ## Update the screenshot in 'README.rst'
	python $< --browser firefox --headless -o $@
	optipng $@

help:  ## Help message for targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
