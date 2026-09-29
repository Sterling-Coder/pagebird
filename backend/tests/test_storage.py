"""`pagebirdy.storage` against an in-memory stand-in for the S3 client, so the
behaviour the API relies on is pinned without any network or bucket."""

import pytest
from botocore.exceptions import ClientError

from pagebirdy import storage

pytestmark = pytest.mark.storage_module


class FakeS3:
    def __init__(self):
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    @staticmethod
    def _no_such_key():
        return ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

    def upload_file(self, path, bucket, key, ExtraArgs=None):
        with open(path, "rb") as f:
            self.objects[key] = f.read()
        self.content_types[key] = (ExtraArgs or {}).get("ContentType")

    def download_file(self, bucket, key, path):
        if key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        with open(path, "wb") as f:
            f.write(self.objects[key])

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise self._no_such_key()

        class Body:
            def __init__(self, data):
                self.data = data

            def read(self):
                return self.data
        return {"Body": Body(self.objects[Key])}

    def delete_object(self, Bucket, Key):
        self.objects.pop(Key, None)

    def delete_objects(self, Bucket, Delete):
        for obj in Delete["Objects"]:
            self.objects.pop(obj["Key"], None)
        return {}

    def get_paginator(self, _name):
        fake = self

        class Paginator:
            def paginate(self, Bucket, Prefix, Delimiter=None):
                contents, prefixes = [], set()
                for key in sorted(fake.objects):
                    if not key.startswith(Prefix):
                        continue
                    rest = key[len(Prefix):]
                    if Delimiter and Delimiter in rest:
                        prefixes.add(Prefix + rest.split(Delimiter)[0] + Delimiter)
                    else:
                        contents.append({"Key": key})
                yield {"Contents": contents,
                       "CommonPrefixes": [{"Prefix": p} for p in sorted(prefixes)]}
        return Paginator()


@pytest.fixture
def s3(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(storage, "_client", fake)
    monkeypatch.setenv("PAGEBIRDY_S3_BUCKET", "docs")
    return fake


def test_the_original_and_the_translation_are_both_kept(s3, tmp_path):
    src, out = tmp_path / "book.idml", tmp_path / "book.ar.idml"
    src.write_bytes(b"english")
    out.write_bytes(b"arabic")
    assert storage.upload_file(str(src), "jobs/j1/book.idml") == "jobs/j1/book.idml"
    storage.upload_file(str(out), "jobs/j1/book.ar.idml")
    assert storage.read_bytes("jobs/j1/book.idml") == b"english"
    assert storage.read_bytes("jobs/j1/book.ar.idml") == b"arabic"


def test_a_pdf_is_stored_with_its_content_type(s3, tmp_path):
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF")
    storage.upload_file(str(src), "jobs/j1/doc.pdf")
    assert s3.content_types["jobs/j1/doc.pdf"] == "application/pdf"


def test_a_missing_object_reads_as_absent_not_as_an_error(s3, tmp_path):
    assert storage.read_bytes("jobs/nope/x.pdf") is None
    target = tmp_path / "x.pdf"
    assert storage.download_to("jobs/nope/x.pdf", str(target)) is False
    assert not target.exists()
    assert not (tmp_path / "x.pdf.part").exists()


def test_download_writes_the_file(s3, tmp_path):
    s3.objects["jobs/j1/a.pdf"] = b"data"
    target = tmp_path / "sub" / "a.pdf"
    assert storage.download_to("jobs/j1/a.pdf", str(target)) is True
    assert target.read_bytes() == b"data"


def test_list_prefix_returns_names_one_level_deep(s3):
    for key in ("jobs/j1/Links/a.psd", "jobs/j1/Links/b.ai",
                "jobs/j1/Links/sub/c.tif", "jobs/j1/Links_ar/a.psd", "jobs/j2/Links/z.psd"):
        s3.objects[key] = b""
    assert sorted(storage.list_prefix("jobs/j1/Links/")) == ["a.psd", "b.ai", "sub"]


def test_deleting_a_job_removes_every_file_under_it_and_nothing_else(s3):
    for key in ("jobs/j1/book.idml", "jobs/j1/Links/a.psd", "jobs/j1/Links_ar/a.psd",
                "jobs/j10/book.idml", "jobs/j2/book.idml"):
        s3.objects[key] = b""
    storage.delete_prefix("jobs/j1/")
    assert sorted(s3.objects) == ["jobs/j10/book.idml", "jobs/j2/book.idml"]


@pytest.mark.parametrize("prefix", ["", "/", "jobs", "jobs/", "jobs//", "/j1/"])
def test_an_unscoped_delete_is_refused(s3, prefix):
    s3.objects["jobs/j1/book.idml"] = b""
    with pytest.raises(ValueError):
        storage.delete_prefix(prefix)
    assert "jobs/j1/book.idml" in s3.objects


def test_an_upload_with_no_bucket_configured_raises(monkeypatch, tmp_path):
    """A job whose files were never stored is not downloadable after a
    restart, so a missing configuration must fail the job, not pass silently."""
    monkeypatch.setattr(storage, "_client", None)
    src = tmp_path / "a.pdf"
    src.write_bytes(b"x")
    with pytest.raises(RuntimeError, match="not configured"):
        storage.upload_file(str(src), "jobs/j1/a.pdf")


def test_region_is_read_from_the_b2_endpoint_when_not_set_explicitly(monkeypatch):
    monkeypatch.delenv("PAGEBIRDY_S3_REGION", raising=False)
    monkeypatch.setenv("PAGEBIRDY_S3_ENDPOINT", "https://s3.us-west-004.backblazeb2.com")
    assert storage._cfg()["region"] == "us-west-004"


def test_an_explicit_region_wins_over_the_endpoint(monkeypatch):
    monkeypatch.setenv("PAGEBIRDY_S3_ENDPOINT", "https://s3.us-west-004.backblazeb2.com")
    monkeypatch.setenv("PAGEBIRDY_S3_REGION", "eu-central-003")
    assert storage._cfg()["region"] == "eu-central-003"


def test_an_endpoint_that_does_not_name_a_region_leaves_it_unresolved(monkeypatch):
    monkeypatch.delenv("PAGEBIRDY_S3_REGION", raising=False)
    monkeypatch.setenv("PAGEBIRDY_S3_ENDPOINT", "https://my-custom-host.example.com")
    assert storage._cfg()["region"] == ""


def test_an_unresolvable_region_raises_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "_client", None)
    monkeypatch.setenv("PAGEBIRDY_S3_ENDPOINT", "https://my-custom-host.example.com")
    monkeypatch.setenv("PAGEBIRDY_S3_BUCKET", "docs")
    monkeypatch.setenv("PAGEBIRDY_S3_ACCESS_KEY", "key")
    monkeypatch.setenv("PAGEBIRDY_S3_SECRET_KEY", "secret")
    monkeypatch.delenv("PAGEBIRDY_S3_REGION", raising=False)
    src = tmp_path / "a.pdf"
    src.write_bytes(b"x")
    with pytest.raises(RuntimeError, match="region"):
        storage.upload_file(str(src), "jobs/j1/a.pdf")
