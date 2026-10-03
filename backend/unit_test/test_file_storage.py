"""Profile picture storage: a folder locally, S3 in a deployment, behind the same routes."""

import io
import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("SMARTFIN_LOG_FILE", "")

import file_storage  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
NAME = "user_7_" + "a" * 32 + ".png"


class FakeS3:
    """The three S3 calls the app makes, kept in a dict."""

    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = (Body, ContentType)

    def delete_object(self, Bucket, Key):
        self.objects.pop((Bucket, Key), None)

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            error = Exception("NoSuchKey")
            error.response = {"Error": {"Code": "NoSuchKey"}}
            raise error
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)][0])}


@pytest.mark.parametrize("name,ok", [
    (NAME, True), ("user_12_" + "0" * 32 + ".webp", True),
    ("../../auth.db", False), ("user_7_short.png", False), ("user_7_" + "a" * 32 + ".exe", False),
    ("profile_pictures/" + NAME, False), ("", False), ("user_x_" + "a" * 32 + ".png", False),
])
def test_only_generated_names_are_accepted(name, ok):
    assert file_storage.is_valid_name(name) is ok


def test_local_storage_round_trip(tmp_path):
    storage = file_storage.LocalStorage(str(tmp_path / "pics"))
    storage.save(NAME, io.BytesIO(PNG))
    assert (tmp_path / "pics" / NAME).read_bytes() == PNG
    storage.delete(NAME)
    storage.delete(NAME)                                   # deleting something already gone is fine
    assert not (tmp_path / "pics" / NAME).exists()


def test_s3_storage_uses_a_private_prefixed_key():
    s3 = FakeS3()
    storage = file_storage.S3Storage("my-bucket", client=s3)
    storage.save(NAME, io.BytesIO(PNG))
    assert s3.objects == {("my-bucket", "profile_pictures/" + NAME): (PNG, "image/png")}
    storage.delete(NAME)
    assert s3.objects == {}


@pytest.fixture
def client(tmp_path):
    """The real app with a throwaway database, logged in as a new user."""
    import subprocess
    code = r'''
import io, json, os, sys
import file_storage
from app import app
from unit_test.test_file_storage import FakeS3, PNG
mode = sys.argv[1]
s3 = FakeS3()
file_storage.set_storage(file_storage.S3Storage("b", client=s3) if mode == "s3" else file_storage.LocalStorage(os.path.join(os.environ["SMARTFIN_DATA_DIR"], "pics")))
c = app.test_client()
c.post("/register", json={"email": "pic@example.com", "password": "Str0ng!Passw0rd"})
h = {"Authorization": "Bearer " + c.post("/login", json={"email": "pic@example.com", "password": "Str0ng!Passw0rd"}).get_json()["token"]}
c.post("/api/profile/create", json={"name": "Pic", "age": 30, "location": "Pune"}, headers=h)
out = {}
def get(u):
    # read and close: on Windows an open response keeps the picture file locked, and replacing it would fail
    r = c.get(u); result = (r.status_code, r.mimetype, r.data); r.close(); return result
def up(data, name):
    return c.post("/api/profile/upload-picture", headers=h, data={"file": (io.BytesIO(data), name)}, content_type="multipart/form-data")
r = up(PNG, "me.png"); out["upload"] = r.status_code; url = r.get_json()["profile_picture_url"]; out["url_shape"] = url.startswith("/uploads/profile_pictures/user_1_")
s_, m_, d_ = get(url); out["serve"] = [s_, m_, d_ == PNG]
r2 = up(PNG + b"2", "again.png"); url2 = r2.get_json()["profile_picture_url"]
out["old_removed"] = get(url)[0]; out["new_served"] = get(url2)[0]
out["stored"] = len(s3.objects) if mode == "s3" else len(os.listdir(os.path.join(os.environ["SMARTFIN_DATA_DIR"], "pics")))
out["bad_type"] = up(b"x", "notes.txt").status_code
out["too_big"] = up(b"0" * (5 * 1024 * 1024 + 1), "big.png").status_code
out["traversal"] = get("/uploads/profile_pictures/..%2F..%2Fauth.db")[0]
out["unknown"] = get("/uploads/profile_pictures/user_1_" + "f" * 32 + ".png")[0]
out["delete"] = c.delete("/api/profile/delete-picture", headers=h).status_code
out["after_delete"] = get(url2)[0]
out["left"] = len(s3.objects) if mode == "s3" else len(os.listdir(os.path.join(os.environ["SMARTFIN_DATA_DIR"], "pics")))
print("RESULT " + json.dumps(out))
'''

    def run(mode):
        env = {**os.environ, "SMARTFIN_DATA_DIR": str(tmp_path / mode), "SMARTFIN_LOG_FILE": "", "DATABASE_URL": "",
               "PYTHONUTF8": "1", "SMARTFIN_UPLOADS_BUCKET": ""}
        out = subprocess.run([sys.executable, "-c", code, mode], cwd=BACKEND, env=env, capture_output=True, text=True, timeout=300)
        line = [ln for ln in out.stdout.splitlines() if ln.startswith("RESULT ")]
        assert out.returncode == 0 and line, out.stderr[-1200:]
        import json
        return json.loads(line[0][7:])
    return run


@pytest.mark.parametrize("mode", ["local", "s3"])
def test_upload_serve_replace_delete_through_the_app(client, mode):
    out = client(mode)
    assert out == {
        "upload": 200, "url_shape": True, "serve": [200, "image/png", True],
        "old_removed": 404, "new_served": 200, "stored": 1,          # replacing a picture removes the old file
        "bad_type": 400, "too_big": 413, "traversal": 404, "unknown": 404,
        "delete": 200, "after_delete": 404, "left": 0,
    }
