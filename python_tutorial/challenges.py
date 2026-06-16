"""Coding challenges mapped to each topic.

Each challenge has:
  - description: what the user needs to do
  - template: starting code (user fills in the blanks)
  - expected_output: the exact expected stdout (None = just practice)
  - hint: hint if they're stuck
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Challenge:
    description: str
    template: str
    expected_output: Optional[str] = None
    hint: str = ""


CHALLENGES: dict[str, list[Challenge]] = {
    # ── Phase 1: Fundamentals ──
    "1.1": [
        Challenge(
            description="Write a Python program that prints 'Hello, Python!' to the screen.",
            template='# Write your code below\nprint("...")',
            expected_output="Hello, Python!\n",
            hint="Use print() with a string inside quotes.",
        ),
        Challenge(
            description="Print your name on one line and your age on the next line.",
            template='# Print name and age on separate lines\nprint("...")',
            expected_output=None,
            hint="Call print() twice, once for each value.",
        ),
    ],
    "1.2": [
        Challenge(
            description="Create two variables `a = 10` and `b = 20`. Print their sum.",
            template="a = 10\nb = 20\n# Calculate and print the sum",
            expected_output="30\n",
            hint="Use print(a + b)",
        ),
        Challenge(
            description="Convert the string '42' to an integer, add 8, and print the result.",
            template='num_str = "42"\nnum_int = int(num_str)\n# Add 8 and print',
            expected_output="50\n",
            hint="num_int + 8 and then print the result.",
        ),
    ],
    "1.3": [
        Challenge(
            description="Print 'Even' if the number 7 is even, else print 'Odd'. Use the modulo operator %.",
            template="num = 7\n# Check if even or odd and print",
            expected_output="Odd\n",
            hint="num % 2 == 0 means even.",
        ),
    ],
    "1.4": [
        Challenge(
            description="Ask the user for their name and print a greeting using an f-string.",
            template='name = input("What is your name? ")\n# Print "Hello, <name>!" using an f-string',
            expected_output=None,
            hint="Use f\"Hello, {name}!\"",
        ),
    ],
    "1.5": [
        Challenge(
            description="Reverse the string 'Python' using slicing and print it.",
            template='word = "Python"\n# Reverse using slicing',
            expected_output="nohtyP\n",
            hint="word[::-1] reverses a string.",
        ),
    ],
    "1.6": [
        Challenge(
            description="Write a function `square(n)` that returns n squared. Call it with 7 and print the result.",
            template="def square(n):\n    # Return n squared\n\nprint(square(7))",
            expected_output="49\n",
            hint="Use return n * n or return n ** 2.",
        ),
    ],
    "1.7": [
        Challenge(
            description="Create a list of numbers [1, 2, 3, 4, 5]. Append 6, then print the sum of all elements.",
            template="nums = [1, 2, 3, 4, 5]\n# Append 6 and print the sum",
            expected_output="21\n",
            hint="nums.append(6), then sum(nums).",
        ),
    ],
    "1.8": [
        Challenge(
            description="Print all even numbers from 1 to 20 using a for loop and range().",
            template="# Print even numbers from 1 to 20\nfor i in range(...):",
            expected_output="2\n4\n6\n8\n10\n12\n14\n16\n18\n20\n",
            hint="range(2, 21, 2) gives even numbers.",
        ),
    ],
    "1.9": [
        Challenge(
            description="Use a list comprehension to create a list of squares for numbers 1 through 10. Print the result.",
            template="squares = [x**2 for x in range(...)]\nprint(squares)",
            expected_output="[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]\n",
            hint="range(1, 11) gives numbers 1 to 10.",
        ),
    ],
    "1.10": [
        Challenge(
            description="Write 'Hello, File!' to a file named 'test.txt', then read and print its content.",
            template='with open("test.txt", "w") as f:\n    f.write("...")\n\nwith open("test.txt", "r") as f:\n    print(f.read())',
            expected_output="Hello, File!\n",
            hint="Write the string 'Hello, File!' to the file.",
        ),
    ],
    # ── Phase 2: Core Python ──
    "2.1": [
        Challenge(
            description="Write a program that handles division by zero. Ask the user for two numbers, divide them, and print the result. If division by zero occurs, print 'Cannot divide by zero!'",
            template="try:\n    a = int(input('Enter a: '))\n    b = int(input('Enter b: '))\n    # Divide and print\nexcept ZeroDivisionError:\n    # Handle error",
            expected_output=None,
            hint="Use ZeroDivisionError in the except block.",
        ),
    ],
    "2.5": [
        Challenge(
            description="Create a dictionary with name 'Alice' and age 30. Convert it to JSON and print it.",
            template='import json\ndata = {"name": "Alice", "age": 30}\n# Convert to JSON string and print',
            expected_output='{"name": "Alice", "age": 30}\n',
            hint="Use json.dumps(data).",
        ),
    ],
    "2.6": [
        Challenge(
            description="Using pathlib, create a directory 'test_dir' and a file inside it named 'hello.txt'. Write 'Hello' to it.",
            template="from pathlib import Path\np = Path('test_dir')\n# Create directory, create file, write to it",
            expected_output=None,
            hint="Use p.mkdir(), then Path('test_dir/hello.txt').write_text('...')",
        ),
    ],
    # ── Phase 3: OOP ──
    "3.1": [
        Challenge(
            description="Create a class `Car` with attributes `brand` and `year`. Create an instance and print its brand.",
            template="class Car:\n    def __init__(self, brand, year):\n        self.brand = brand\n        self.year = year\n\nmy_car = Car('Toyota', 2020)\n# Print the brand",
            expected_output="Toyota\n",
            hint="Use print(my_car.brand).",
        ),
    ],
    "3.4": [
        Challenge(
            description="Create a parent class `Animal` with a method `speak()`. Create a child class `Dog` that overrides `speak()`. Call speak on a Dog instance.",
            template="class Animal:\n    def speak(self):\n        return '...'\n\nclass Dog(Animal):\n    def speak(self):\n        return '...'\n\n# Create Dog instance and call speak",
            expected_output="Woof!\n",
            hint="Make Dog.speak() return 'Woof!'.",
        ),
    ],
    "3.7": [
        Challenge(
            description="Create a class `Book` with `__str__` returning 'Title by Author'. Create an instance and print it.",
            template='class Book:\n    def __init__(self, title, author):\n        self.title = title\n        self.author = author\n\n    def __str__(self):\n        return f"..."\n\nbook = Book("1984", "George Orwell")\nprint(book)',
            expected_output="1984 by George Orwell\n",
            hint="Return f'{self.title} by {self.author}'.",
        ),
    ],
    # ── Phase 4: Intermediate ──
    "4.2": [
        Challenge(
            description="Use map() with a lambda to convert a list of temperatures in Celsius [0, 20, 30, 40] to Fahrenheit. Formula: F = C * 9/5 + 32.",
            template="celsius = [0, 20, 30, 40]\nfahrenheit = list(map(lambda c: ..., celsius))\nprint(fahrenheit)",
            expected_output="[32.0, 68.0, 86.0, 104.0]\n",
            hint="lambda c: c * 9/5 + 32",
        ),
    ],
    "4.6": [
        Challenge(
            description="Write a generator function `countdown(n)` that yields numbers from n down to 1. Use it to print a countdown from 5.",
            template="def countdown(n):\n    while n > 0:\n        yield n\n        n -= 1\n\nfor num in countdown(5):\n    ...",
            expected_output="5\n4\n3\n2\n1\n",
            hint="Print num inside the for loop.",
        ),
    ],
    # ── Phase 5: Advanced ──
    "5.1": [
        Challenge(
            description="Write a decorator `uppercase` that converts the return value of a function to uppercase. Apply it to a function `greet()` that returns 'hello world'.",
            template="def uppercase(func):\n    def wrapper():\n        result = func()\n        return result.upper()\n    return wrapper\n\n@uppercase\ndef greet():\n    return 'hello world'\n\nprint(greet())",
            expected_output="HELLO WORLD\n",
            hint="The decorator already handles it — just print greet().",
        ),
    ],
    "5.2": [
        Challenge(
            description="Use a context manager (with statement) to open a file and write 'Learning Python!' to it. Then verify the content by printing it.",
            template='with open("output.txt", "w") as f:\n    f.write("...")\n\nwith open("output.txt", "r") as f:\n    ...',
            expected_output="Learning Python!\n",
            hint="Print f.read() in the second with block.",
        ),
    ],
    # ── Phase 6: Engineering ──
    "6.1": [
        Challenge(
            description="Use the requests library to fetch https://httpbin.org/get and print the status code.",
            template="import requests\nresponse = requests.get('https://httpbin.org/get')\n# Print the status code",
            expected_output="200\n",
            hint="Use print(response.status_code).",
        ),
    ],
    "6.3": [
        Challenge(
            description="Write a function `add(a, b)` and test it using an assert statement.",
            template="def add(a, b):\n    return a + b\n\n# Use assert to test add(2, 3) == 5\n# Use assert to test add(-1, 1) == 0\nprint('All tests passed!')",
            expected_output="All tests passed!\n",
            hint="assert add(2, 3) == 5, assert add(-1, 1) == 0",
        ),
    ],
    # ── Phase 7: AI Engineering ──
    "7.1": [
        Challenge(
            description="Create a NumPy array of shape (3, 3) filled with zeros, then set the middle element to 1. Print the array.",
            template="import numpy as np\narr = np.zeros((3, 3))\n# Set the middle element (index [1,1]) to 1\nprint(arr)",
            expected_output="[[0. 0. 0.]\n [0. 1. 0.]\n [0. 0. 0.]]\n",
            hint="Use arr[1, 1] = 1",
        ),
    ],
    "7.2": [
        Challenge(
            description="Create a Pandas DataFrame from a dictionary with columns 'Name' and 'Age', then print the DataFrame.",
            template="import pandas as pd\ndata = {'Name': ['Alice', 'Bob'], 'Age': [25, 30]}\ndf = pd.DataFrame(data)\nprint(df)",
            expected_output="    Name  Age\n0  Alice   25\n1    Bob   30\n",
            hint="The code is mostly done — just print df.",
        ),
    ],
}


def get_challenge(phase: int, topic: int) -> Optional["Challenge"]:
    """Get the first challenge for a given phase.topic."""
    key = f"{phase}.{topic}"
    challenges = CHALLENGES.get(key, [])
    return challenges[0] if challenges else None


def get_all_challenges(phase: int, topic: int) -> list["Challenge"]:
    """Get all challenges for a given phase.topic."""
    key = f"{phase}.{topic}"
    return CHALLENGES.get(key, [])


def show_challenge(challenge: Challenge, console) -> None:
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown as RichMD
    from rich.console import Console as RichConsole

    md = RichMD(challenge.description)
    panel = Panel(
        f"[bold cyan]🎯 Challenge[/]",
        border_style="cyan",
    )
    console.print(panel)
    console.print(md)
    if challenge.template:
        console.print("\n[bold]Starting code:[/]")
        console.print(Syntax(challenge.template.strip(), "python", theme="monokai"))
