.PHONY: flake8 example test coverage translatable_strings update_translations

style:
	isort .
	black --target-version=py35 .
	flake8

style_check:
	isort -c .
	black --target-version=py35 --check .

flake8:
	flake8

example:
	python example/manage.py runserver

eslint: package-lock.json
	npx eslint --ignore-path .gitignore .

package-lock.json: package.json
	npm install

test:
	DJANGO_SETTINGS_MODULE=tests.settings \
		python -m django test $${TEST_ARGS:-tests}

test_selenium:
	DJANGO_SELENIUM_TESTS=true DJANGO_SETTINGS_MODULE=tests.settings \
		python -m django test $${TEST_ARGS:-tests}

coverage:
	python --version
	coverage erase
	DJANGO_SETTINGS_MODULE=tests.settings \
		python -b -W always -m coverage run -m django test -v2 $${TEST_ARGS:-tests}
	coverage report
	coverage html

translatable_strings:
	cd debug_toolbar && python -m django makemessages -l en --no-obsolete
	@echo "Please commit changes and run 'tx push -s' (or wait for Transifex to pick them)"

update_translations:
	tx pull -a --minimum-perc=10
	cd debug_toolbar && python -m django compilemessages
