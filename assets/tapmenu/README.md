# ipython-tapmenu

Jupytier notebook extention that adds "TAP Help" menu to the notebook toolbar.

The menu follows the following structure
- TAP Help
  - ATK Client Install
    - From PyPi Central(install code snippet)
      - List of last 5 weekly/Production builds
    - From ATK Server(install code snippet)
  - Credentials File(code snippet)
  - ATK Client Documentation
  - ATK Git
  - Jira
  - TAP Home Page

Can be installed through the jupyter-nbextensions CLI.

To install the plugin
```
jupyter-nbextension install tapmenu
```

Once it's installed you will have to enable it
```
jupyter-nbextensio enable tapmenu/main
```
