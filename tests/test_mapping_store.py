from jira_migrator.mapping_store import MappingStore


def test_mapping_store_roundtrip(tmp_path):
    db = tmp_path / "mappings.sqlite3"
    store = MappingStore(str(db))

    store.set_project_map("SRC", "DST")
    store.set_issue_map("SRC-1", "DST-1")
    store.set_field_map("customfield_10010", "customfield_20020")

    assert store.get_project_map("SRC") == "DST"
    assert store.get_issue_map("SRC-1") == "DST-1"
    assert store.get_field_map("customfield_10010") == "customfield_20020"
