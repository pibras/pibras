BEGIN;
SET LOCAL search_path = mbras, public;
DO $$
DECLARE org uuid; tenant uuid; request uuid; rec uuid := gen_random_uuid(); caught text;
        partner uuid; propagation uuid; bad_ref text;
BEGIN
  INSERT INTO organization (name) VALUES ('Synthetic DSAR test') RETURNING id INTO org;
  INSERT INTO tenant (organization_id,name) VALUES (org,'Synthetic tenant') RETURNING id INTO tenant;
  -- Open deletion and completed access do not require resolution evidence.
  INSERT INTO data_subject_request (tenant_id,request_type,due_at)
    VALUES (tenant,'deletion',now()) RETURNING id INTO request;
  INSERT INTO data_subject_request (tenant_id,request_type,status,due_at)
    VALUES (tenant,'access','fulfilled',now());
  BEGIN
    UPDATE data_subject_request SET status='fulfilled', affected_record_ids=ARRAY[rec] WHERE id=request;
    RAISE EXCEPTION 'accepted fulfilled deletion without resolution action';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS caught=CONSTRAINT_NAME;
    IF caught <> 'dsr_fulfilled_deletion_evidence' THEN RAISE; END IF;
  END;
  BEGIN
    UPDATE data_subject_request SET status='fulfilled', resolution_action='anonymize' WHERE id=request;
    RAISE EXCEPTION 'accepted fulfilled deletion with zero affected IDs';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS caught=CONSTRAINT_NAME;
    IF caught <> 'dsr_fulfilled_deletion_evidence' THEN RAISE; END IF;
  END;
  BEGIN
    UPDATE data_subject_request SET affected_record_ids=ARRAY[rec,NULL] WHERE id=request;
    RAISE EXCEPTION 'accepted null affected ID';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS caught=CONSTRAINT_NAME;
    IF caught <> 'dsr_record_ids_shape' THEN RAISE; END IF;
  END;
  BEGIN
    UPDATE data_subject_request SET affected_record_ids=ARRAY[[rec]] WHERE id=request;
    RAISE EXCEPTION 'accepted nested affected ID array';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS caught=CONSTRAINT_NAME;
    IF caught <> 'dsr_record_ids_shape' THEN RAISE; END IF;
  END;
  BEGIN
    UPDATE data_subject_request SET affected_record_ids=NULL WHERE id=request;
    RAISE EXCEPTION 'accepted NULL affected_record_ids array';
  EXCEPTION WHEN not_null_violation THEN NULL; END;
  UPDATE data_subject_request SET status='fulfilled',resolution_action='anonymize',
         affected_record_ids=ARRAY[rec] WHERE id=request;
  INSERT INTO organization (name) VALUES ('Synthetic DSAR partner') RETURNING id INTO partner;
  INSERT INTO partner_relationship (tenant_id,partner_organization_id,role,contract_ref,dpa_ref,
    effective_from,dsar_contact_ref,retention_period_days)
    VALUES (tenant,partner,'operator','contract:test','dpa:test',current_date,'contact:test',0)
    RETURNING id INTO partner;
  INSERT INTO dsar_propagation (request_id,partner_relationship_id,due_at)
    VALUES (request,partner,now()) RETURNING id INTO propagation;

  FOREACH bad_ref IN ARRAY ARRAY[NULL::text, '', E' \t\n', U&'\00A0\3000'] LOOP
    BEGIN
      UPDATE dsar_propagation SET status='fulfilled', fulfilled_at=now(), external_reference=bad_ref
        WHERE id=propagation;
      RAISE EXCEPTION 'accepted fulfilled propagation without external evidence';
    EXCEPTION WHEN check_violation THEN
      GET STACKED DIAGNOSTICS caught=CONSTRAINT_NAME;
      IF caught <> 'propagation_fulfilled_evidence' THEN RAISE; END IF;
    END;
  END LOOP;
  UPDATE dsar_propagation SET status='fulfilled', fulfilled_at=now(), external_reference='receipt:synthetic'
    WHERE id=propagation;
END $$;
ROLLBACK;
