"""Unit tests for alias command"""


def test__empty_list(runner, conf):
    """Should show empty aliases"""
    result = runner(f"-c {conf} alias ls")
    assert result.exit_code == 0
    assert result.output == ""


def test__add_alias_ok(runner, conf, address):
    """Should add an alias"""
    password = "password"
    result = runner(f"-c {conf} alias add local", input=f"{address}\n{password}\n\n")
    assert result.exit_code == 0

    result = runner(f"-c {conf} alias ls")
    assert result.exit_code == 0
    assert result.output == "local\n"


def test__add_alias_with_options(runner, conf, address):
    """Should add an alias"""
    password = "password"
    result = runner(f"-c {conf} alias add -A {address} -p {password} -b bucket local")
    assert result.exit_code == 0

    result = runner(f"-c {conf} alias ls")
    assert result.exit_code == 0
    assert result.output == "local\n"


def test__add_alias_twice(runner, conf, address):
    """Should not add an alias if the name already exists"""
    result = runner(f"-c {conf} alias add local", input=f"{address}\npassword\n\n")
    assert result.exit_code == 0

    result = runner(f"-c {conf} alias add local")
    assert result.exit_code == 1
    assert result.output == "Alias 'local' already exists\nAborted!\n"


def test__rm_ok(runner, conf, address):
    """Should remove alias"""
    result = runner(f"-c {conf} alias add local", input=f"{address}\npassword\n\n")
    assert result.exit_code == 0

    result = runner(f"-c {conf} alias rm local")
    assert result.exit_code == 0

    result = runner(f"-c {conf} alias ls")
    assert result.exit_code == 0
    assert result.output == ""


def test__rm_not_exist(runner, conf):
    """Shouldn't remove alias if it doesn't exist"""
    result = runner(f"-c {conf} alias rm local")
    assert result.exit_code == 1
    assert result.output == "Alias 'local' doesn't exist\nAborted!\n"


def test__show(runner, conf, address):
    """Should show alias"""
    result = runner(f"-c {conf} alias add local", input=f"{address}\npassword\n\n")
    assert result.exit_code == 0

    result = runner(f"-c {conf} alias show local")
    assert result.exit_code == 0
    assert result.output.replace(" ", "") == f"Address:127.0.0.1\nBucket:data\n"


def test__show_not_exist(runner, conf):
    """Should not show alias if alias doesn't exist"""
    result = runner(f"-c {conf} alias show local")
    assert result.exit_code == 1
    assert result.output == "Alias 'local' doesn't exist\nAborted!\n"
