**Steps to create python project**
* Create project folder (with or without command line)
* Navigate to folder with cmd and open VS Code in project location using command "Code ."
* Enable virtual environment. Open command pallette (Ctrl + Shift + P). Type "Python: Create Environment". Select "Venv", then select latest python version installed.
    * A virtual environment isolates projects so any installed libraries don't interfere with other project envs or the global interpreter env.
    * An environment folder (/.venv) will be created in the project root.

To Run current file, open command pallete (ctrl + shift + p), type "Run Python File"

**To Debug, use following commands**
* F5 - Run Debugger
* F10 - Step over
* F11 - Step into
* Shift+F11 - Step out
* Shit+F5 - Terminate debugger
* Ctrl+Shift+F5 - Restart debugger

**Managing dependencies across environments**
When working on Python projects, it’s essential to manage your dependencies effectively. One useful tip is to use the "pip freeze > requirements.txt" command.
his command helps you create a requirements.txt file that lists all the packages installed in your virtual environment. This file can then be used to recreate the same environment elsewhere.
Furthermore, you can continue to add dependencies to it as your project may grow in complexity using command "pip install -r requirements.txt"
By following these steps, you ensure that your project dependencies are consistent across different environments, making it easier to collaborate with others and deploy your project.

**Useful shortcuts**
* Ctrl+R: Helps switch between projects by opening a list of recently opened folders and workspaces.
* Ctrl+Shift+`: Open command prompt for your selected terminal
* Ctrl+Shift+P: Open VS code command pallette
* ctrl+Shift+x: Open extensions

**Other Tips**
* VS code comes with a "Python Profile" that you can enable. A good starting point for Python development as it sets up a lot of pre-requisites: extensions, libraries, settings, etc.

**Typical Python Project Structure**
my_project/
├── src/
│   ├── my_package/
│   │   ├── __init__.py
│   │   ├── module1.py
│   │   └── utils.py
├── tests/
│   ├── test_module1.py
│   └── test_utils.py
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
└── LICENSE
