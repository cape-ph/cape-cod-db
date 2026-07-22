from urllib.parse import quote

from sqlalchemy.engine import make_url

from cape_cod_db.db_url import resolve_db_url


def test_resolve_db_url_accepts_percent_encoded_passwords():
    raw_passwords = [
        "pa%ss1",
        "pa@ss1",
        "pa:ss1",
        "pa/ss1",
        "pa ss1",
        "pa#ss1",
        "pa?ss1",
        "p%ss@w:o/rd #?x",
    ]

    for raw_password in raw_passwords:
        encoded_password = quote(raw_password, safe="")
        url = f"postgresql://user:{encoded_password}@host:5432/db"

        assert resolve_db_url({}, {}, url) == url, raw_password
        assert make_url(url).password == raw_password, raw_password
