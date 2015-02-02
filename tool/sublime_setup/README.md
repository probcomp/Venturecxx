## Venture in Sublime Text 3
This document contains instructions to allow users to configure Sublime Text 3 for proper Venture syntax highlighting and indentation.
TODO: Write an actual package to automate all of this.

To optimally configure Venture for Sublime Text, do the following:

* Install the "lispindent" plugin using the package manager.
* Install the AAAPackageDev using the package manager.

### Syntax highlighting
* Select Tools -> Packages -> Package Development -> New Syntax Definition; this will create a new YAML-tmLanguage file.
* Fill in the following fields:
    - name: Venture
    - sourceName: source.venture
    - fileTypes: [vnt]
* To fill in the "patterns" section, call `python venture_patterns.py syntax` from the directory containing this document, and paste the output below the "patterns:" field in the YAML-tmLanguage file you've created.
    - TODO: There are some commands that will appear in multiple places; e.g. "assume" can be a directive, an inference macro, and an inference SP. Maybe fix this later using scopes.
* Save the file as `venture.YAML-tmLanguage` in your Sublime Text User preferences folder, which on my Mac is here: `~/Library/Application Support/Sublime Text 3/Packages/User`
* Press F7, and a .tmLanguage file will be created in the same directory.

### Indentation
* In the directory with your User Preferences, open the file lispindent.sublime-settings.

Add the following entry:

    "venture": {
        "detect": ".*\\.(vnt)$",
        "default_indent": "function",
        "regex": [<regex>]
    }

Fill the regex list field with the output of `python venture_patterns.py indent`

### Sublime Settings
In the User Preferences directory, create a file named `venture.sublime-settings` and paste in the following:

    {
        "extensions": [ "vnt" ],
        "tab_size": 2
    }

### Commenting with cmd + /
In the User Preferences directory, create a file named `Comments.YAML-tmPreferences` and paste in the following:

    name: Comments
    scope: source.venture
    settings:
      shellVariables:
      - name: TM_COMMENT_START
        value: '; '

* From the command menu (cmd + shift + p), select `AAAPackageDev: Convert (YAML, JSON, Plist) to...`
* Select `Convert to: Property List`. This will save a .tmPreferences file.

### Finishing up
Restart Sublime Text. Venture should now be fully supported and available as a syntax mode.

