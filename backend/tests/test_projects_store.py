from babel.models import Segment
from babel.review.store import ReviewStore


def _seg(sid, source, target, status="approved"):
    return Segment(id=sid, page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                   source=source, target=target, placeholders={}, status=status)


def _store(tmp_path):
    return ReviewStore(str(tmp_path / "review.db"), tm_path=str(tmp_path / "tm.db"))


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
