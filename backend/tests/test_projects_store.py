from pagebirdy.models import Segment
from pagebirdy.review.store import ReviewStore


def _seg(sid, source, target, status="approved"):
    return Segment(id=sid, page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                   source=source, target=target, placeholders={}, status=status)


def _store(tmp_path):
    return ReviewStore(str(tmp_path / "review.db"))


def test_create_and_list_project(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Kindergarten_10Pages", job_type="document",
                             source_lang="en", target_lang="zh-Hant")
    projects = st.list_projects()
    assert len(projects) == 1
    assert projects[0]["id"] == pid
    assert projects[0]["name"] == "Kindergarten_10Pages"
    assert projects[0]["job_type"] == "document"
    assert projects[0]["target_lang"] == "zh-Hant"
    assert projects[0]["file_count"] == 0
    assert projects[0]["status_counts"] == {}


def test_get_project_missing_returns_none(tmp_path):
    st = _store(tmp_path)
    assert st.get_project("does-not-exist") is None


def test_save_job_with_project_rolls_up_into_project(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Kindergarten_10Pages")
    jid = st.save_job("in.pdf", "out.pdf",
                       [_seg("a", "Hello", "Hola", status="approved")],
                       {}, project_id=pid, job_type="document")

    project = st.get_project(pid)
    assert project["file_count"] == 1
    assert project["status_counts"] == {"approved": 1}

    jobs = st.list_jobs()
    assert jobs[0]["id"] == jid


def test_save_job_without_project_still_works(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf",
                       [_seg("a", "Hello", "Hola")], {})
    jobs = st.list_jobs()
    assert jobs[0]["id"] == jid


def test_get_job_history_spans_all_segments(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf",
                       [_seg("a", "Hello", "Hello", status="needs_human"),
                        _seg("b", "World", "World", status="needs_human")],
                       {})
    st.update_segment(jid, "a", "Hola", approve=True, reviewer="ana")
    st.update_segment(jid, "b", "Mundo", approve=True, reviewer="luis")

    hist = st.get_job_history(jid)
    assert len(hist) == 2
    seg_ids = {h["seg_id"] for h in hist}
    assert seg_ids == {"a", "b"}
    assert hist[0]["created_at"] >= hist[1]["created_at"]


def test_create_and_list_folders(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    fid = st.create_folder(pid, "HAHA")

    folders = st.list_folders(pid)
    assert len(folders) == 1
    assert folders[0]["id"] == fid
    assert folders[0]["name"] == "HAHA"
    assert st.get_folder(fid)["project_id"] == pid


def test_files_scoped_to_folder(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    fid = st.create_folder(pid, "HAHA")

    root_jid = st.save_job("root.pdf", "out.pdf", [_seg("a", "Hi", "Hi")], {},
                            project_id=pid, folder_id=None)
    in_folder_jid = st.save_job("in_folder.pdf", "out.pdf", [_seg("a", "Hi", "Hi")], {},
                                 project_id=pid, folder_id=fid)

    jobs = st.list_jobs()
    root_job = next(j for j in jobs if j["id"] == root_jid)
    folder_job = next(j for j in jobs if j["id"] == in_folder_jid)
    assert root_job["folder_id"] is None
    assert folder_job["folder_id"] == fid


def test_nested_folders(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    root_fid = st.create_folder(pid, "Parent")
    child_fid = st.create_folder(pid, "Child", parent_folder_id=root_fid)

    root_level = st.list_folders(pid)
    assert len(root_level) == 1
    assert root_level[0]["id"] == root_fid

    nested = st.list_folders(pid, parent_folder_id=root_fid)
    assert len(nested) == 1
    assert nested[0]["id"] == child_fid

    assert st.get_folder(child_fid)["parent_folder_id"] == root_fid
    assert st.get_folder(root_fid)["parent_folder_id"] is None


def test_delete_folder_removes_its_files(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    fid = st.create_folder(pid, "HAHA")
    jid = st.save_job("in.pdf", "out.pdf", [_seg("a", "Hi", "Hi")], {},
                       project_id=pid, folder_id=fid)

    st.delete_folder(fid)

    assert st.get_folder(fid) is None
    assert all(j["id"] != jid for j in st.list_jobs())


def test_delete_folder_recurses_into_subfolders(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    parent_fid = st.create_folder(pid, "Parent")
    child_fid = st.create_folder(pid, "Child", parent_folder_id=parent_fid)
    jid = st.save_job("in.pdf", "out.pdf", [_seg("a", "Hi", "Hi")], {},
                       project_id=pid, folder_id=child_fid)

    st.delete_folder(parent_fid)

    assert st.get_folder(parent_fid) is None
    assert st.get_folder(child_fid) is None
    assert all(j["id"] != jid for j in st.list_jobs())


def test_delete_folder_with_edited_job_does_not_violate_fk(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    fid = st.create_folder(pid, "HAHA")
    jid = st.save_job("in.pdf", "out.pdf",
                       [_seg("a", "Hello", "Hello", status="needs_human")],
                       {}, project_id=pid, folder_id=fid)
    st.update_segment(jid, "a", "Hola", approve=True, reviewer="ana")

    st.delete_folder(fid)

    assert st.get_folder(fid) is None
    assert all(j["id"] != jid for j in st.list_jobs())


def test_set_project_target_lang_if_unset(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    assert st.get_project(pid)["target_lang"] is None

    st.set_project_target_lang_if_unset(pid, "es")
    assert st.get_project(pid)["target_lang"] == "es"

    st.set_project_target_lang_if_unset(pid, "fr")
    assert st.get_project(pid)["target_lang"] == "es"


def test_delete_job_with_edit_history_does_not_violate_fk(tmp_path):
    """A job with segment_events (an edit/approve trail) must still delete
    cleanly — segment_events has a real FK to jobs, so deleting the job
    without first clearing its events trips SQLite's FK constraint."""
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf",
                       [_seg("a", "Hello", "Hello", status="needs_human")], {})
    st.update_segment(jid, "a", "Hola", approve=True, reviewer="ana")
    assert st.get_job_history(jid) != []

    st.delete_job(jid)

    assert all(j["id"] != jid for j in st.list_jobs())


def test_delete_project_with_edited_job_does_not_violate_fk(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    jid = st.save_job("in.pdf", "out.pdf",
                       [_seg("a", "Hello", "Hello", status="needs_human")],
                       {}, project_id=pid)
    st.update_segment(jid, "a", "Hola", approve=True, reviewer="ana")

    st.delete_project(pid)

    assert st.get_project(pid) is None
    assert all(j["id"] != jid for j in st.list_jobs())


def test_delete_project_removes_folders_too(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    st.create_folder(pid, "HAHA")

    st.delete_project(pid)

    assert st.list_folders(pid) == []


def test_delete_project_removes_project_and_its_jobs(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("Testing")
    jid = st.save_job("in.pdf", "out.pdf",
                       [_seg("a", "Hello", "Hola", status="approved")],
                       {}, project_id=pid, job_type="document")

    st.delete_project(pid)

    assert st.get_project(pid) is None
    assert all(j["id"] != jid for j in st.list_jobs())
    assert st.get_segments(jid) == []


def test_list_jobs_filters_by_project_and_folder_in_sql(tmp_path):
    st = _store(tmp_path)
    owner = "owner-" + __import__("uuid").uuid4().hex
    p1 = st.create_project("p1", created_by=owner)
    p2 = st.create_project("p2", created_by=owner)
    folder = st.create_folder(p1, "f", created_by=owner)
    root = st.save_job("a.pdf", "", [], {}, project_id=p1, created_by=owner)
    inside = st.save_job("b.pdf", "", [], {}, project_id=p1, folder_id=folder, created_by=owner)
    other = st.save_job("c.pdf", "", [], {}, project_id=p2, created_by=owner)

    ids = lambda **kw: {j["id"] for j in st.list_jobs(created_by=owner, **kw)}
    assert ids() == {root, inside, other}
    assert ids(project_id=p1) == {root, inside}
    assert ids(project_id=p1, folder_id=None) == {root}
    assert ids(project_id=p1, folder_id=folder) == {inside}
    assert ids(project_id=p2, folder_id=None) == {other}


def test_get_job_returns_one_job_or_none(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("a.pdf", "", [_seg("s1", "hi", "hola")], {"k": 1})
    job = st.get_job(jid)
    assert job["id"] == jid
    assert job["meta"] == {"k": 1}
    assert job["status_counts"] == {"approved": 1}
    assert st.get_job("does-not-exist") is None


def test_close_returns_connection_to_pool_and_is_idempotent(tmp_path, monkeypatch):
    import pagebirdy.review.store as store_mod

    monkeypatch.setattr(store_mod, "_pools", {})
    st = _store(tmp_path)
    pool = store_mod._get_pool()
    try:
        st.close()
        st.close()
        pool.wait()
        size = pool.get_stats()["pool_size"]
        for _ in range(5):
            again = _store(tmp_path)
            assert again.list_projects() is not None
            again.close()
        assert pool.get_stats()["pool_size"] == size  # reused, not reopened
    finally:
        pool.close()


def test_get_project_counts_jobs_with_and_without_segments(tmp_path):
    st = _store(tmp_path)
    pid = st.create_project("counts")
    st.save_job("a.pdf", "", [_seg("s1", "a", "b"), _seg("s2", "c", "d", "needs_human")],
                {}, project_id=pid)
    st.save_job("b.pdf", "", [], {}, project_id=pid)
    project = st.get_project(pid)
    assert project["file_count"] == 2
    assert project["status_counts"] == {"approved": 1, "needs_human": 1}
    assert st.get_project_row(pid)["id"] == pid
    assert st.get_project_row("nope") is None


def test_pool_recovers_a_connection_the_server_closed(tmp_path, monkeypatch):
    import pagebirdy.review.store as store_mod

    monkeypatch.setattr(store_mod, "_pools", {})
    st = _store(tmp_path)
    pool = store_mod._get_pool()
    try:
        conn = st.conn
        pid = conn.info.backend_pid
        st.close()
        other = store_mod.psycopg.connect(store_mod._db_url(), autocommit=True)
        other.execute("SELECT pg_terminate_backend(%s)", (pid,))
        other.close()
        store_mod._last_used[conn] = 0.0  # looks long idle, so it is re-checked
        fresh = _store(tmp_path)
        try:
            assert fresh.conn is not conn
            assert fresh.list_projects() is not None
        finally:
            fresh.close()
    finally:
        pool.close()


def test_assert_owns_project_light_and_full(tmp_path, monkeypatch):
    import pytest
    from fastapi import HTTPException

    import pagebirdy.api as api

    monkeypatch.setattr(api, "effective_owner_ids", lambda uid: [uid])
    st = _store(tmp_path)
    pid = st.create_project("mine", created_by="u1")
    st.save_job("a.pdf", "", [_seg("s1", "a", "b")], {}, project_id=pid, created_by="u1")

    assert api._assert_owns_project(st, pid, {"id": "u1"})["id"] == pid
    full = api._assert_owns_project(st, pid, {"id": "u1"}, full=True)
    assert full["file_count"] == 1 and full["status_counts"] == {"approved": 1}
    with pytest.raises(HTTPException) as e:
        api._assert_owns_project(st, pid, {"id": "u2"})
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        api._assert_owns_project(st, "nope", {"id": "u1"}, full=True)
    assert e.value.status_code == 404
