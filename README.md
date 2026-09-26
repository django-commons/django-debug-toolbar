# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/django-commons/django-debug-toolbar/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|---------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| debug\_toolbar/\_\_init\_\_.py                      |        4 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/\_compat.py                          |       18 |        5 |        6 |        1 |     75% |  5-12, 36 |
| debug\_toolbar/\_stubs.py                           |       18 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/apps.py                              |      111 |        4 |       40 |        2 |     96% |150, 187-188, 254 |
| debug\_toolbar/decorators.py                        |       28 |        0 |        6 |        0 |    100% |           |
| debug\_toolbar/forms.py                             |       24 |        0 |        2 |        0 |    100% |           |
| debug\_toolbar/management/\_\_init\_\_.py           |        0 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/management/commands/\_\_init\_\_.py  |        0 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/management/commands/debugsqlshell.py |       19 |        0 |        2 |        0 |    100% |           |
| debug\_toolbar/middleware.py                        |      118 |        8 |       50 |        4 |     93% |45, 48, 61-63, 77-81, 97 |
| debug\_toolbar/migrations/0001\_initial.py          |        4 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/migrations/\_\_init\_\_.py           |        0 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/models.py                            |       12 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/\_\_init\_\_.py               |       90 |        3 |       10 |        2 |     95% |44, 105, 124, 135-\>exit |
| debug\_toolbar/panels/alerts.py                     |       70 |        0 |       28 |        1 |     99% | 134-\>132 |
| debug\_toolbar/panels/cache.py                      |      109 |        1 |       32 |        2 |     98% |90-\>exit, 102 |
| debug\_toolbar/panels/community.py                  |        7 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/headers.py                    |       23 |        0 |        2 |        0 |    100% |           |
| debug\_toolbar/panels/history/\_\_init\_\_.py       |        2 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/history/forms.py              |        4 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/history/panel.py              |       63 |        2 |        8 |        0 |     97% |     88-90 |
| debug\_toolbar/panels/history/views.py              |       38 |        0 |       12 |        0 |    100% |           |
| debug\_toolbar/panels/profiling.py                  |      109 |        9 |       24 |        2 |     92% |31, 34-35, 55, 65, 120-121, 128-129 |
| debug\_toolbar/panels/redirects.py                  |       33 |        0 |        4 |        0 |    100% |           |
| debug\_toolbar/panels/request.py                    |       34 |        0 |        6 |        0 |    100% |           |
| debug\_toolbar/panels/settings.py                   |       19 |        2 |        0 |        0 |     89% |     14-15 |
| debug\_toolbar/panels/signals.py                    |       46 |        3 |       14 |        3 |     90% |58, 76-77, 86-\>88 |
| debug\_toolbar/panels/sql/\_\_init\_\_.py           |        2 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/sql/forms.py                  |       77 |        7 |       14 |        4 |     86% |23-28, 38, 43-\>49, 45, 50 |
| debug\_toolbar/panels/sql/panel.py                  |      176 |       10 |       50 |        4 |     93% |52, 80, 232-237, 278-279, 320-\>exit |
| debug\_toolbar/panels/sql/tracking.py               |      137 |        5 |       38 |        2 |     96% |142-\>146, 156, 239-240, 278, 284 |
| debug\_toolbar/panels/sql/utils.py                  |       89 |        0 |       32 |        1 |     99% | 32-\>exit |
| debug\_toolbar/panels/sql/views.py                  |       69 |        3 |       14 |        3 |     93% |45, 71, 107 |
| debug\_toolbar/panels/staticfiles.py                |       83 |        2 |       22 |        1 |     97% |123-125, 146-\>145 |
| debug\_toolbar/panels/tasks.py                      |       32 |        0 |        8 |        0 |    100% |           |
| debug\_toolbar/panels/templates/\_\_init\_\_.py     |        2 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/templates/jinja2.py           |       14 |        0 |        2 |        1 |     94% | 21-\>exit |
| debug\_toolbar/panels/templates/panel.py            |      135 |        9 |       42 |        8 |     90% |20-\>31, 31-\>39, 42, 159, 163, 176-179, 200-201, 208-\>214, 209-\>213 |
| debug\_toolbar/panels/templates/views.py            |       46 |        2 |       10 |        1 |     95% |35-\>32, 59-60 |
| debug\_toolbar/panels/timer.py                      |       67 |        5 |       12 |        5 |     85% |11-12, 31-34, 70-\>72, 87-\>89, 89-\>117, 117-\>120 |
| debug\_toolbar/panels/versions.py                   |       43 |        1 |       14 |        1 |     96% |        65 |
| debug\_toolbar/sanitize.py                          |        6 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/settings.py                          |       36 |        2 |        6 |        1 |     93% |   103-104 |
| debug\_toolbar/store.py                             |      266 |       10 |       42 |        7 |     94% |42-46, 57-\>59, 173-174, 190-\>exit, 214-\>exit, 244, 275, 318, 322-\>exit |
| debug\_toolbar/templatetags/\_\_init\_\_.py         |        0 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/templatetags/debug\_toolbar.py       |       24 |        3 |        8 |        4 |     78% |15, 29, 31, 34-\>36 |
| debug\_toolbar/toolbar.py                           |      150 |        5 |       38 |        1 |     96% |119-127, 174-\>186, 226 |
| debug\_toolbar/urls.py                              |        4 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/utils.py                             |      214 |        7 |       68 |        8 |     95% |30, 61, 121, 125-\>128, 144-\>143, 195-196, 200, 216 |
| debug\_toolbar/views.py                             |       20 |        0 |        2 |        0 |    100% |           |
| **TOTAL**                                           | **2695** |  **108** |  **668** |   **69** | **94%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/django-commons/django-debug-toolbar/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/django-commons/django-debug-toolbar/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/django-commons/django-debug-toolbar/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/django-commons/django-debug-toolbar/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fdjango-commons%2Fdjango-debug-toolbar%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/django-commons/django-debug-toolbar/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.