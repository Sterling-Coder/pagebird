import logging

from fastapi.testclient import TestClient

import babel.api as api


def _client(tmp_path):
    api._REVIEW_DB = str(tmp_path / "review.db")
    api._TM_DB = str(tmp_path / "tm.db")
    return TestClient(api.app)


def test_create_and_list_project(tmp_path):
    client = _client(tmp_path)
    res = client.post("/api/projects", json={
        "name": "Kindergarten_10Pages", "job_type": "document",
        "target_lang": "zh-Hant",
    })
    assert res.status_code == 200
    project_id = res.json()["id"]

    res = client.get("/api/projects")
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert project_id in ids


def test_get_project_404(tmp_path):
    client = _client(tmp_path)
    res = client.get("/api/projects/does-not-exist")
    assert res.status_code == 404


def test_get_job_404(tmp_path):
    client = _client(tmp_path)
    res = client.get("/api/jobs/does-not-exist")
    assert res.status_code == 404


def test_get_logs_returns_new_lines_since_cursor(tmp_path):
    client = _client(tmp_path)
    logging.getLogger("babel.api").info("marker-one")
    res = client.get("/api/logs")
    assert res.status_code == 200
    lines = res.json()["lines"]
    assert any("marker-one" in l["line"] for l in lines)
    last_id = lines[-1]["id"]

    logging.getLogger("babel.api").info("marker-two")
    res = client.get("/api/logs", params={"since": last_id})
    lines2 = res.json()["lines"]
    assert any("marker-two" in l["line"] for l in lines2)
    assert not any("marker-one" in l["line"] for l in lines2)


def test_delete_job(tmp_path):
    from babel.models import Segment
    from babel.review.store import ReviewStore

    client = _client(tmp_path)
    seg = Segment(id="a", page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                  source="Hi", target="Hi", placeholders={}, status="approved")
    jid = ReviewStore(api._REVIEW_DB, tm_path=api._TM_DB).save_job(
        "in.pdf", "out.pdf", [seg], {})

    res = client.delete(f"/api/jobs/{jid}")
    assert res.status_code == 200

    res = client.get(f"/api/jobs/{jid}")
    assert res.status_code == 404


def test_delete_job_404(tmp_path):
    client = _client(tmp_path)
    res = client.delete("/api/jobs/does-not-exist")
    assert res.status_code == 404


def test_project_files_empty_for_new_project(tmp_path):
    client = _client(tmp_path)
    res = client.post("/api/projects", json={"name": "Empty", "job_type": "document"})
    project_id = res.json()["id"]

    res = client.get(f"/api/projects/{project_id}/files")
    assert res.status_code == 200
    assert res.json() == []


def test_delete_project(tmp_path):
    client = _client(tmp_path)
    res = client.post("/api/projects", json={"name": "Testing", "job_type": "document"})
    project_id = res.json()["id"]

    res = client.delete(f"/api/projects/{project_id}")
    assert res.status_code == 200

    res = client.get(f"/api/projects/{project_id}")
    assert res.status_code == 404


def test_job_history_endpoint(tmp_path):
    from babel.models import Segment
    from babel.review.store import ReviewStore

    client = _client(tmp_path)
    seg = Segment(id="a", page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                  source="Hello", target="Hello", placeholders={}, status="needs_human")
    jid = ReviewStore(api._REVIEW_DB, tm_path=api._TM_DB).save_job(
        "in.pdf", "out.pdf", [seg], {})

    client.patch(f"/api/segments/{jid}/a",
                 json={"target": "Hola", "approve": True, "reviewer": "ana"})

    res = client.get(f"/api/jobs/{jid}/history")
    assert res.status_code == 200
    hist = res.json()
    assert len(hist) == 1
    assert hist[0]["seg_id"] == "a"
    assert hist[0]["reviewer"] == "ana"


def test_create_and_list_folders(tmp_path):
    client = _client(tmp_path)
    project_id = client.post("/api/projects", json={"name": "Testing"}).json()["id"]

    res = client.post(f"/api/projects/{project_id}/folders", json={"name": "HAHA"})
    assert res.status_code == 200
    folder_id = res.json()["id"]

    res = client.get(f"/api/projects/{project_id}/folders")
    assert res.status_code == 200
    names = [f["name"] for f in res.json()]
    assert "HAHA" in names
    assert res.json()[0]["id"] == folder_id


def test_create_folder_404_for_missing_project(tmp_path):
    client = _client(tmp_path)
    res = client.post("/api/projects/does-not-exist/folders", json={"name": "X"})
    assert res.status_code == 404


def test_nested_folder_via_api(tmp_path):
    client = _client(tmp_path)
    project_id = client.post("/api/projects", json={"name": "Testing"}).json()["id"]
    parent_id = client.post(f"/api/projects/{project_id}/folders", json={"name": "Parent"}).json()["id"]

    res = client.post(f"/api/projects/{project_id}/folders",
                       json={"name": "Child", "parent_folder_id": parent_id})
    assert res.status_code == 200
    child_id = res.json()["id"]
    assert res.json()["parent_folder_id"] == parent_id

    res = client.get(f"/api/projects/{project_id}/folders")
    assert [f["id"] for f in res.json()] == [parent_id]

    res = client.get(f"/api/projects/{project_id}/folders", params={"parent_folder_id": parent_id})
    assert [f["id"] for f in res.json()] == [child_id]

    res = client.get(f"/api/folders/{child_id}")
    assert res.status_code == 200
    assert res.json()["id"] == child_id

    res = client.get("/api/folders/does-not-exist")
    assert res.status_code == 404


def test_create_folder_404_for_missing_parent(tmp_path):
    client = _client(tmp_path)
    project_id = client.post("/api/projects", json={"name": "Testing"}).json()["id"]
    res = client.post(f"/api/projects/{project_id}/folders",
                       json={"name": "X", "parent_folder_id": "does-not-exist"})
    assert res.status_code == 404


def test_delete_folder(tmp_path):
    client = _client(tmp_path)
    project_id = client.post("/api/projects", json={"name": "Testing"}).json()["id"]
    folder_id = client.post(f"/api/projects/{project_id}/folders", json={"name": "HAHA"}).json()["id"]

    res = client.delete(f"/api/folders/{folder_id}")
    assert res.status_code == 200

    res = client.get(f"/api/folders/{folder_id}")
    assert res.status_code == 404


def test_delete_folder_404(tmp_path):
    client = _client(tmp_path)
    res = client.delete("/api/folders/does-not-exist")
    assert res.status_code == 404


def test_list_files_scoped_by_folder(tmp_path):
    from babel.models import Segment
    from babel.review.store import ReviewStore

    client = _client(tmp_path)
    project_id = client.post("/api/projects", json={"name": "Testing"}).json()["id"]
    folder_id = client.post(f"/api/projects/{project_id}/folders", json={"name": "HAHA"}).json()["id"]

    seg = Segment(id="a", page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                  source="Hi", target="Hi", placeholders={}, status="approved")
    store = ReviewStore(api._REVIEW_DB, tm_path=api._TM_DB)
    root_jid = store.save_job("root.pdf", "out.pdf", [seg], {}, project_id=project_id)
    folder_jid = store.save_job("in.pdf", "out.pdf", [seg], {},
                                 project_id=project_id, folder_id=folder_id)

    res = client.get(f"/api/projects/{project_id}/files")
    root_ids = [j["id"] for j in res.json()]
    assert root_jid in root_ids
    assert folder_jid not in root_ids

    res = client.get(f"/api/projects/{project_id}/files", params={"folder_id": folder_id})
    folder_ids = [j["id"] for j in res.json()]
    assert folder_jid in folder_ids
    assert root_jid not in folder_ids

    res = client.get(f"/api/projects/{project_id}/files", params={"all": "true"})
    all_ids = [j["id"] for j in res.json()]
    assert root_jid in all_ids
    assert folder_jid in all_ids


def test_delete_project_404(tmp_path):
    client = _client(tmp_path)
    res = client.delete("/api/projects/does-not-exist")
    assert res.status_code == 404
