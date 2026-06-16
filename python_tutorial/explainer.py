"""Explain Python errors in plain English with fix suggestions."""

EXPLANATIONS: dict[str, dict] = {
    "SyntaxError": {
        "title": "Syntax Error",
        "explanation": (
            "Python couldn't understand your code because it doesn't follow the language's grammar rules. "
            "This is like a grammatical error in a sentence."
        ),
        "common_causes": [
            "Missing colon (:) at end of if/for/while/def lines",
            "Unmatched parentheses, brackets, or quotes",
            "Using = instead of == in comparisons",
            "Indentation that doesn't match (mixing tabs and spaces)",
        ],
        "fixes": [
            "Check the line BEFORE the error - Python often points to where it got confused, not where the problem started",
            "Count your opening and closing brackets/parentheses",
            "Use a linter (like flake8) to catch syntax issues",
        ],
    },
    "IndentationError": {
        "title": "Indentation Error",
        "explanation": (
            "Python uses indentation (spaces/tabs) to define blocks of code. "
            "Your indentation doesn't line up correctly."
        ),
        "common_causes": [
            "Mixing tabs and spaces (Python 3 disallows this)",
            "A block has inconsistent indentation levels",
            "Forgot to indent code inside a function/loop/if block",
        ],
        "fixes": [
            "Use 4 spaces for each indentation level (configure your editor)",
            "Never use tabs - set your editor to convert tabs to spaces",
            "Look for lines that should be indented but aren't, or vice versa",
        ],
    },
    "NameError": {
        "title": "Name Error",
        "explanation": (
            "You're trying to use a variable, function, or module name that Python doesn't recognize. "
            "It hasn't been defined yet, or you've spelled it wrong."
        ),
        "common_causes": [
            "Typo in the variable name (e.g., 'printt' instead of 'print')",
            "Using a variable before assigning a value to it",
            "Forgetting to import a module before using it",
            "Variable defined inside a function but used outside (scope issue)",
        ],
        "fixes": [
            "Check the spelling - Python names are case-sensitive",
            "Make sure you've assigned the variable before this line",
            "If it's a function from a module, check you imported it",
            "Variables created inside functions aren't accessible outside",
        ],
    },
    "TypeError": {
        "title": "Type Error",
        "explanation": (
            "You're trying to perform an operation on a value of the wrong type. "
            "For example, adding a string to a number, or calling something that isn't a function."
        ),
        "common_causes": [
            "Adding str + int (e.g., 'age is ' + 25 - convert 25 to str first)",
            "Calling a non-function like it's a function (e.g., 'hello'() )",
            "Passing wrong type to a function (e.g., len(5) instead of len('hello'))",
            "Trying to index into a non-sequence (e.g., 42[0])",
        ],
        "fixes": [
            "Use str(), int(), float() to convert between types",
            "Check what type a variable is with type(variable)",
            "Read function documentation to see what types it expects",
        ],
    },
    "ValueError": {
        "title": "Value Error",
        "explanation": (
            "You passed an acceptable type, but the value itself is invalid. "
            "For example, trying to convert 'hello' to an integer."
        ),
        "common_causes": [
            "int('abc') - string isn't a valid number",
            "list.index(99) when 99 isn't in the list",
            "Removing an element that doesn't exist with .remove()",
        ],
        "fixes": [
            "Validate input before conversion (e.g., check if string is numeric)",
            "Use if x in list before calling .index() or .remove()",
            "Wrap in try/except to handle expected errors gracefully",
        ],
    },
    "IndexError": {
        "title": "Index Error",
        "explanation": (
            "You tried to access an element at a position that doesn't exist. "
            "Like asking for the 10th item in a 5-item list."
        ),
        "common_causes": [
            "Using an index that's too large (e.g., my_list[10] when it has 5 items)",
            "Off-by-one errors - remember lists start at 0",
            "Empty list - trying to access index 0 of an empty list",
        ],
        "fixes": [
            "Check the list length with len(list) before indexing",
            "Remember: indexes go from 0 to len-1",
            "Negative indexes go from -1 (last) to -len (first)",
        ],
    },
    "KeyError": {
        "title": "Key Error",
        "explanation": (
            "You tried to access a dictionary key that doesn't exist. "
            "Like looking up a word in a dictionary that isn't there."
        ),
        "common_causes": [
            "Typo in the key name",
            "Forgetting what keys are in the dictionary",
            "The key might have been added conditionally or removed",
        ],
        "fixes": [
            "Use .get(key, default) instead of dict[key] to avoid crashes",
            "Check with 'if key in dict:' before accessing",
            "Print dict.keys() to see what's available",
        ],
    },
    "AttributeError": {
        "title": "Attribute Error",
        "explanation": (
            "You're trying to access an attribute or method that doesn't exist on this object. "
            "Like calling .upper() on a number - numbers don't have that method."
        ),
        "common_causes": [
            "Calling a method on the wrong type (e.g., 'hello'.append() - strings don't have append)",
            "Typo in the method/attribute name",
            "Using .append on a tuple instead of a list (tuples are immutable)",
        ],
        "fixes": [
            "Check the type of the object with type()",
            "Use dir(object) to see all available methods/attributes",
            "Remember: tuples, strings, and ints are immutable - they don't have modification methods",
        ],
    },
    "ModuleNotFoundError": {
        "title": "Module Not Found",
        "explanation": (
            "Python can't find the module you're trying to import. "
            "It's either not installed or you've spelled it wrong."
        ),
        "common_causes": [
            "The module isn't installed (need to pip install it)",
            "Typo in the module name",
            "You're in the wrong virtual environment",
            "Your file is named the same as a module (shadowing)",
        ],
        "fixes": [
            "Install it: pip install <module_name>",
            "Check the spelling - module names are case-sensitive",
            "Make sure your file isn't named 'requests.py' when you're trying to import requests",
            "Activate the right virtual environment",
        ],
    },
    "FileNotFoundError": {
        "title": "File Not Found",
        "explanation": (
            "Python tried to open a file that doesn't exist at the path you specified. "
            "Either the path is wrong or the file hasn't been created yet."
        ),
        "common_causes": [
            "The file doesn't exist at that location",
            "You're looking in the wrong directory",
            "Typo in the filename or path",
        ],
        "fixes": [
            "Check the current directory: import os; print(os.getcwd())",
            "Use an absolute path or check the relative path carefully",
            "Use pathlib for more reliable path handling",
        ],
    },
    "ZeroDivisionError": {
        "title": "Zero Division Error",
        "explanation": (
            "You tried to divide a number by zero, which is mathematically undefined."
        ),
        "common_causes": [
            "A variable you expected to be non-zero turned out to be zero",
            "Input value wasn't validated before division",
        ],
        "fixes": [
            "Check the divisor before dividing: if x != 0: result = a / x",
            "Catch the error: try: result = a / x except ZeroDivisionError: ...",
        ],
    },
    "ImportError": {
        "title": "Import Error",
        "explanation": (
            "Python found the module, but couldn't import a specific name from it. "
            "The function/class you're trying to import doesn't exist in that module."
        ),
        "common_causes": [
            "Typo in the name being imported",
            "The name was removed in a newer version of the module",
            "You need to import from a submodule, not the top-level module",
        ],
        "fixes": [
            "Check the spelling of the imported name",
            "Check the module documentation for the correct import path",
            "Use dir(module) to see available names",
        ],
    },
    "StopIteration": {
        "title": "Stop Iteration",
        "explanation": (
            "An iterator ran out of items. This is normal when a for loop finishes, "
            "but it crashes if you're calling next() manually without handling it."
        ),
        "common_causes": [
            "Calling next() on an iterator that has no more items",
        ],
        "fixes": [
            "Use a for loop instead of manual next() calls",
            "Catch StopIteration when using next() manually",
            "Provide a default: next(iterator, 'default_value')",
        ],
    },
}


FALLBACK = {
    "title": "Runtime Error",
    "explanation": (
        "Your code encountered an error during execution. "
        "The traceback above shows what went wrong and where."
    ),
    "common_causes": [
        "A logic error in your code",
        "Unexpected input or state",
        "Missing edge case handling",
    ],
    "fixes": [
        "Read the traceback from bottom to top - the last line is usually the cause",
        "Add print() statements to check variable values before the crash",
        "Break complex operations into smaller steps to isolate the problem",
    ],
}


def explain_error(error_line: str, traceback_text: str = "") -> dict:
    """Given an error traceback, return a human-friendly explanation."""
    # Extract error type from traceback
    error_type = None
    for line in traceback_text.splitlines():
        line = line.strip()
        for known in EXPLANATIONS:
            if line.startswith(known) or known in line:
                error_type = known
                break
        if error_type:
            break

    if not error_type and error_line:
        for known in EXPLANATIONS:
            if known.lower() in error_line.lower():
                error_type = known
                break

    if not error_type:
        # Try to find any recognizable error pattern
        for known in EXPLANATIONS:
            if known in error_line or known.replace("Error", "") in error_line:
                error_type = known
                break

    info = EXPLANATIONS.get(error_type, FALLBACK)

    # Try to extract the specific name/value from the error
    details = ""
    if error_type == "NameError" and "'" in error_line:
        name = error_line.split("'")[1] if len(error_line.split("'")) > 1 else ""
        if name:
            details = f"\n\n[bold]The name '{name}' doesn't exist.[/] Check the spelling or define it before using it."
    elif error_type == "KeyError" and "'" in error_line:
        key = error_line.split("'")[1] if len(error_line.split("'")) > 1 else ""
        if key:
            details = f"\n\n[bold]The key '{key}' wasn't found in the dictionary.[/] Check available keys with .keys()."

    return {
        "title": info["title"],
        "explanation": info["explanation"] + details,
        "common_causes": info["common_causes"],
        "fixes": info["fixes"],
    }
