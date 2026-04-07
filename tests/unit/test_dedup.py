"""Unit tests for deduplication module."""

from src.dedup import init_db, filter_new, save_seen, get_all_seen_ids


def test_filter_new_returns_all_on_empty_db(in_memory_db, sample_entries):
    """On empty DB, all entries are new."""
    result = filter_new(sample_entries, db_path=in_memory_db)
    assert len(result) == len(sample_entries)


def test_filter_new_removes_known_ids(in_memory_db, sample_entries):
    """Known IDs are filtered out."""
    save_seen(sample_entries[:1], db_path=in_memory_db)

    result = filter_new(sample_entries, db_path=in_memory_db)
    assert len(result) == len(sample_entries) - 1
    assert sample_entries[0] not in result


def test_save_seen_persists_entries(in_memory_db, sample_entries):
    """Saved entries appear in get_all_seen_ids."""
    save_seen(sample_entries, db_path=in_memory_db)

    seen_ids = get_all_seen_ids(db_path=in_memory_db)
    for entry in sample_entries:
        assert entry["id"] in seen_ids


def test_no_duplicates_after_double_save(in_memory_db, sample_entries):
    """Saving the same entries twice doesn't create duplicates."""
    save_seen(sample_entries, db_path=in_memory_db)
    save_seen(sample_entries, db_path=in_memory_db)

    seen_ids = get_all_seen_ids(db_path=in_memory_db)
    assert len(seen_ids) == len(sample_entries)
