# A→B manifest contract test

- Manifest version: `1.0`
- Result: PASS

| Check | Result | Detail |
|---|---|---|
| build_SI_paper | PASS | `{"paper_id": "doi:10.1021/acs.iecr.4c03980", "doi_status": "present", "pdf_sha256": "119aaf3d99e00082", "si_status": "present", "si_files": 1, "errors": []}` |
| load_SI_text | PASS | `{"chars": 4891, "parsed_files": 1}` |
| build_no_SI_paper | PASS | `{"paper_id": "doi:10.1021/je00005a025", "si_status": "missing", "errors": []}` |
| reject_pdf_hash_mismatch | PASS | `{"errors": ["pdf.sha256 mismatch: expected 0000000000000000000000000000000000000000000000000000000000000000, got 119aaf3d99e000826e42f88c8242a1ea5e6860071fb4794c075196c2a82d202f"]}` |
| reject_SI_hash_mismatch | PASS | `{"errors": ["si.sha256 mismatch: data/raw_si/10.1021_acs.iecr.4c03980/si_01.pdf"]}` |
| reject_present_DOI_without_value | PASS | `{"errors": ["doi.value invalid for present status: None", "doi.status present but value is empty"]}` |
| missing_DOI_allowed | PASS | `{"paper_id": "pdf:8558972992c38f88", "doi": {"value": null, "status": "missing", "source": null}, "warnings": ["DOI could not be established from A metadata or filename"]}` |
| load_stored_manifest | PASS | `{"source": "stored"}` |
| load_all_pdfs | PASS | `{"pdfs": 29, "legacy": 0, "stored": 29}` |
| legacy_manifest_fallback | PASS | `{"source": "legacy", "warnings": ["No stored manifest found; generated a legacy manifest for this PDF"]}` |
