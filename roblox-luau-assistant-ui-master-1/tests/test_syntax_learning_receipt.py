from scripts.syntax_learning_receipt import make_receipt

def test_receipt_has_all_fields_and_sanitizes_private_values():
    r=make_receipt(failure_class='extra end',root_cause='composition mismatch',actual_repair='removed duplicate terminator',source_truth_confirmation='current source reloaded',validation_result='SYNTAX_REVALIDATED',regression_status='SYNTAX_REGRESSION_ADDED',generalization='nested callbacks can drift during composition',prevention_rule='whole-source balance audit',evidence_status='STATICALLY_VERIFIED',reusable=True)
    assert r['reusable'] is True
    assert '[REDACTED]' not in r['generalization']
    r2=make_receipt(failure_class='x',root_cause='y',actual_repair='z',source_truth_confirmation='TWOPARTYGAMER path',validation_result='x',regression_status='x',generalization='x',prevention_rule='x',evidence_status='CANDIDATE',reusable=False)
    assert 'TWOPARTYGAMER' not in r2['source_truth_confirmation']
