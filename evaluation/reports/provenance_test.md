# Provenance test (temporary database)

- Result: PASS
- B-flow batch: `D:/database1/evaluation/artifacts/b_flow/batches/batch_20261124_225303`

| Check | Result | Detail |
|---|---|---|
| imported_tests | PASS | `{"tests": 8, "raw_records": 8, "import_output": "导入完成： {'inserted': 8, 'skipped': 0, 'failed': 0, 'compound_new': 4, 'recipe_new': 4, 'source_new': 1, 'source_location_new': 8, 'test_new': 8, 'performance_new': 8} 批次： provenance_test\n"}` |
| qc_record_initialized | PASS | `{"qc_rows": 8}` |
| excerpt_path_set | PASS | `{"with_path": 8}` |
| sidecar_hashes | PASS | `{"sidecars": 8}` |
| same_paper_records_not_crosslinked | PASS | `{"matched": 8}` |
| distinct_sidecars_per_record | PASS | `{"groups": 1}` |
| trace_new_records | PASS | `{"traced": [{"test_id": 1, "source": "sidecar", "chars": 134}, {"test_id": 2, "source": "sidecar", "chars": 141}, {"test_id": 3, "source": "sidecar", "chars": 145}]}` |
| backup_reload | PASS | `{}` |
| corrupt_sidecar_reported | PASS | `{"warnings": ["excerpt sidecar hash_mismatch: D:\\database1\\evaluation\\artifacts\\provenance\\run\\corrupt.json"], "source": "snapshot"}` |
| missing_sidecar_reported | PASS | `{"warnings": ["excerpt sidecar missing: D:\\database1\\evaluation\\artifacts\\provenance\\run\\missing.json"], "source": "snapshot"}` |
| legacy_snapshot_fallback | PASS | `{"legacy": {"3": {"source": "sidecar", "match": null, "chars": 622, "warnings": []}, "24": {"source": "snapshot", "match": "whitelist_row", "chars": 148, "warnings": ["source_location.excerpt_path is NULL (legacy record)"]}, "27": {"source": "snapshot", "match": "whitelist_row", "chars": 127, "warnings": ["source_location.excerpt_path is NULL (legacy record)"]}, "31": {"source": "snapshot", "match": "table_row", "chars": 95, "warnings": ["source_location.excerpt_path is NULL (legacy record)"]}}}` |
| all_L2_traceable | PASS | `{"l2": 38, "resolved_l2": 38, "sources_l2": {"sidecar": 1, "snapshot": 37}}` |
| all_tests_traceable | PASS | `{"tests": 63, "resolved": 63, "sources": {"batch_jsonl": 25, "sidecar": 1, "snapshot": 37}}` |
| qc_record_backfill_temp | PASS | `{"dry_count": 8, "qc_rows": 8, "unverified": 8}` |
| human_review_interface_temp | PASS | `{"qc": [1, "test_reviewer"], "review_file": true}` |
| excerpt_backfill_main_copy | PASS | `{"paths": 60, "sidecars": 59, "main_db_unchanged": true}` |
| export_fields | PASS | `{"l2_records": 4}` |

The temporary database is under `evaluation/artifacts/provenance/run`; the main `data/ccus.sqlite` was not written.
