# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/django-commons/django-debug-toolbar/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|---------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| debug\_toolbar/\_\_init\_\_.py                      |        4 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/\_compat.py                          |       11 |        0 |        2 |        0 |    100% |           |
| debug\_toolbar/\_stubs.py                           |       18 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/apps.py                              |      110 |        4 |       40 |        2 |     96% |150, 181, 188-189 |
| debug\_toolbar/decorators.py                        |       28 |        0 |        6 |        0 |    100% |           |
| debug\_toolbar/forms.py                             |       24 |        0 |        2 |        0 |    100% |           |
| debug\_toolbar/management/\_\_init\_\_.py           |        0 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/management/commands/\_\_init\_\_.py  |        0 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/management/commands/debugsqlshell.py |       19 |        0 |        2 |        0 |    100% |           |
| debug\_toolbar/middleware.py                        |      113 |        6 |       50 |        5 |     93% |49, 53, 67-72, 88, 209->214 |
| debug\_toolbar/migrations/0001\_initial.py          |        4 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/migrations/\_\_init\_\_.py           |        0 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/models.py                            |       12 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/\_\_init\_\_.py               |       85 |        3 |       10 |        2 |     95% |44, 98, 108, 119->exit |
| debug\_toolbar/panels/alerts.py                     |       69 |        0 |       28 |        1 |     99% |  133->131 |
| debug\_toolbar/panels/cache.py                      |      102 |        1 |       26 |        5 |     95% |48->exit, 86->exit, 98, 204->206, 217->216 |
| debug\_toolbar/panels/community.py                  |        6 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/headers.py                    |       22 |        0 |        2 |        1 |     96% |    42->44 |
| debug\_toolbar/panels/history/\_\_init\_\_.py       |        2 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/history/forms.py              |        4 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/history/panel.py              |       57 |        5 |        8 |        0 |     92% |70-72, 117-119 |
| debug\_toolbar/panels/history/views.py              |       38 |        0 |       12 |        0 |    100% |           |
| debug\_toolbar/panels/profiling.py                  |      106 |        8 |       28 |        5 |     90% |31, 34-35, 55, 65, 76, 119, 127 |
| debug\_toolbar/panels/redirects.py                  |       35 |        0 |        6 |        0 |    100% |           |
| debug\_toolbar/panels/request.py                    |       33 |        0 |        6 |        0 |    100% |           |
| debug\_toolbar/panels/settings.py                   |       13 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/signals.py                    |       45 |        3 |       14 |        3 |     90% |58, 75-76, 85->87 |
| debug\_toolbar/panels/sql/\_\_init\_\_.py           |        2 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/sql/forms.py                  |       87 |       16 |       16 |        4 |     77% |25-30, 33-38, 41-46, 56, 61->67, 63, 68 |
| debug\_toolbar/panels/sql/panel.py                  |      176 |       10 |       50 |        4 |     93% |53, 81, 232-237, 279-280, 321->exit |
| debug\_toolbar/panels/sql/tracking.py               |      117 |        4 |       30 |        1 |     97% |125->129, 201-202, 240, 246 |
| debug\_toolbar/panels/sql/utils.py                  |       98 |        2 |       38 |        3 |     96% |30->exit, 155, 162 |
| debug\_toolbar/panels/sql/views.py                  |       68 |        3 |       14 |        3 |     93% |44, 70, 106 |
| debug\_toolbar/panels/staticfiles.py                |       82 |        2 |       22 |        1 |     97% |122-124, 145->144 |
| debug\_toolbar/panels/templates/\_\_init\_\_.py     |        2 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/panels/templates/jinja2.py           |       14 |        0 |        2 |        1 |     94% |  21->exit |
| debug\_toolbar/panels/templates/panel.py            |      134 |        9 |       42 |        8 |     90% |20->31, 31->39, 42, 158, 162, 175-178, 199-200, 207->213, 208->212 |
| debug\_toolbar/panels/templates/views.py            |       46 |        2 |       10 |        1 |     95% |35->32, 59-60 |
| debug\_toolbar/panels/timer.py                      |       61 |        5 |       10 |        4 |     85% |11-12, 31-34, 65->67, 82->84, 84->112 |
| debug\_toolbar/panels/versions.py                   |       42 |        1 |       14 |        1 |     96% |        64 |
| debug\_toolbar/sanitize.py                          |        6 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/settings.py                          |       36 |        2 |        6 |        1 |     93% |    99-100 |
| debug\_toolbar/store.py                             |      140 |        7 |       14 |        3 |     92% |133-138, 152->exit, 176->exit, 206 |
| debug\_toolbar/templatetags/\_\_init\_\_.py         |        0 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/toolbar.py                           |      141 |        6 |       30 |        1 |     95% |104-112, 159->171, 211-214 |
| debug\_toolbar/urls.py                              |        4 |        0 |        0 |        0 |    100% |           |
| debug\_toolbar/utils.py                             |      214 |        7 |       68 |        8 |     95% |30, 61, 121, 125->128, 144->143, 195-196, 200, 215 |
| debug\_toolbar/views.py                             |       19 |        0 |        2 |        0 |    100% |           |
|                                           **TOTAL** | **2449** |  **106** |  **610** |   **68** | **94%** |           |


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