from python_tutorial.sandbox import run_code


class TestSandbox:
    def test_hello_world(self):
        result = run_code("print('hello')")
        assert result["success"] is True
        assert "hello" in result["stdout"]

    def test_syntax_error(self):
        result = run_code("def foo(")
        assert result["success"] is False
        assert result["stderr"]

    def test_timeout(self):
        result = run_code("import time; time.sleep(10)", timeout=1)
        assert result["success"] is False
        assert "timed out" in result["stderr"]

    def test_blocked_open(self):
        result = run_code("open('/tmp/test.txt')")
        assert result["success"] is False
        assert "blocked" in result["stderr"] or "allowed" in result["stderr"]

    def test_blocked_os_system(self):
        result = run_code("import os; os.system('ls')")
        assert result["success"] is False

    def test_blocked_subprocess(self):
        result = run_code("import subprocess; subprocess.run(['ls'])")
        assert result["success"] is False

    def test_blocked_socket(self):
        result = run_code("import socket; s=socket.socket(); s.connect(('localhost',80))")
        assert result["success"] is False

    def test_blocked_eval(self):
        result = run_code("eval('1+1')")
        assert result["success"] is False
        assert "blocked" in result["stderr"].lower()

    def test_blocked_exec(self):
        result = run_code("exec('x=1')")
        assert result["success"] is False
        assert "blocked" in result["stderr"].lower()

    def test_blocked_breakpoint(self):
        result = run_code("breakpoint()")
        assert result["success"] is False
        assert "blocked" in result["stderr"].lower()

    def test_output_limit(self):
        result = run_code("for i in range(100000): print('x' * 100)")
        # Should not crash with memory error
        assert len(result["stdout"]) < 200_000

    def test_import_stdlib(self):
        result = run_code("import json; print(json.dumps({'a': 1}))")
        assert result["success"] is True
        assert '{"a": 1}' in result["stdout"]

    def test_multiline_code(self):
        result = run_code("""
x = 1
y = 2
print(x + y)
""")
        assert result["success"] is True
        assert "3" in result["stdout"]
