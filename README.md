# Haruki

A hata discord application generated using its `scaffold` command:
```sh
$ hata scaffold Haruki haruki
```

## What is hata scaffold?

Hata scaffold is used to automatically create a basic structure for your application.
This includes code, configuration files, and other necessary files and assets.

Even tho scaffold command is helpful to get a head start when building your application, it is still
important to remember that the generated code should be always reviewed and modified as needed to ensure
that it meets the requirements.

## Directory structure

```
root
├─ .gitignore
├─ README.md
├─ pyproject.toml
└─ haruki
    ├─ .env
    ├─ __init__.py
    ├─ __main__.py
    ├─ cli.py
    ├─ constants.py
    ├─ bots
    │   ├─ __init__.py
    │   └─ haruki.py
    └─ plugins
        ├─ __init__.py
        └─ ping.py
```

### ./gitignore

A gitignore file specifies intentionally untracked files that Git should ignore. Files already tracked by
Git are not affected, so make sure after updating it you `git add ".gitignore"` before anything else. Each
line in a gitignore file specifies a pattern.

### ./README.md

A README file is an essential guide that gives a detailed description of your project.

### ./pyproject.toml

A text file that specifies what build dependencies your package needs.

### ./haruki/

The directory that contains your discord application.

### ./haruki/.env

A `.env` file is a text file containing key - value pairs of environment variables. This file is normally
included with a project, but not committed to source.

`.env` files are used to store sensitive credentials. Your discord applications' tokens are loaded from
here too, so make sure it is populated correctly before starting your project.

### ./haruki/\_\_init\_\_.py

This is a special python file that is used to indicate that the directory should be treated as package.
It defines what can be directly imported from your package. Leaving it completely empty is also fine.

### ./haruki/\_\_main\_\_.py

Often a python program is executed using `$ python3 project.py`. If your program is inside of a directory
that has a `__main__.py` file then it can be ran using `$ python3 -m project`.

### ./haruki/cli.py

Contains the *command line interface* code, basically the main function is defined here.

### ./haruki/constants.py

Stores the constant and the configuration variables. Variables from the `.env` file are loaded here.
This kind of setup allows you to keep the sensitive configuration data separate from your code and customize
the behavior of your application based on the environment settings.

### ./haruki/bots/

This directory contains the bots ran by your discord application.

### ./haruki/bots/\_\_init\_\_.py

Imports the defined bots in the directory.

To import a bot from here do either:
```py
from haruki.bots import Haruki # absolute import
```
or
```py
from ..bots import Haruki # relative import
```

### ./haruki/bots/haruki.py

Haruki is initialized here and should be configured here too. As in which intents and extensions it uses.
This file should also define all core functionality that is required by plugins to correctly integrate.

### ./haruki/plugins/

Plugins are components of the application that add a specific functionality to it.
They are modules, meaning they can be added or removed as required without modifying the core codebase.

Plugins can be defined in both standalone file or in package format as well:
```
plugins
├─ __init__.py
└─ my_plugin_0.py
└─ my_plugin_1
    ├─ __init__.py
    └─ file_n.py
```

### ./haruki/plugins/\_\_init\_\_.py

This `__init__.py` is required for cross-plugin imports.

The difference between this and other `__init__.py` files in a plugin directory is that here we mark the
directory as a plugin root, meaning this file will NOT stop additional files (or directories) to be
identified as plugins.

### ./haruki/plugins/ping.py

An example single-file plugin.

Registers a `/ping` command into every client.

## Install

```
$ python3 -m pip install .
```

## Running CLI

```
$ python3 -m haruki help
```
or
```
$ haruki help
```
