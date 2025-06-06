-- ============================================================================
--  DM3: Foreign Key & Primary Key Constraints
--  Author      : Gokul Thothathri
--  Reviewer    : Senior Developer (Commented Version)
--  Purpose     : Establish referential integrity according to DM3 ER diagram [https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/]
--  Date        : 06.06.2025
-- ============================================================================


-- ============================================================================
-- (Blue) MODULE: INSURANCE MASTER & PERSON RECORDS (VERS)
-- ============================================================================

-- Ensure PSID is the unique identifier for a person
ALTER TABLE vers
ADD CONSTRAINT pk_vers_psid PRIMARY KEY ("PSID");

-- Each quarterly insurance record in VERSQ must belong to a person in VERS
ALTER TABLE versq
ADD CONSTRAINT fk_versq_vers FOREIGN KEY ("PSID") REFERENCES vers("PSID");

-- Each DMP participation record must match a VERSQ entry (by PSID + quarter)
ALTER TABLE versq
ADD CONSTRAINT uq_versq_psid_versq UNIQUE ("PSID", "VERSQ");

ALTER TABLE versqdmp
ADD CONSTRAINT fk_versqdmp_versq FOREIGN KEY ("PSID", "VERSQ")
REFERENCES versq("PSID", "VERSQ");

-- Each prescription (REZ) belongs to a person in VERS
ALTER TABLE rez
ADD CONSTRAINT fk_rez_vers FOREIGN KEY ("PSID") REFERENCES vers("PSID");

-- Each outpatient case (AMB) is associated with a person
ALTER TABLE ambfall
ADD CONSTRAINT fk_ambfall_vers FOREIGN KEY ("PSID") REFERENCES vers("PSID");

-- Each hospital case (KH) is linked optionally to a person
ALTER TABLE khfall
ADD CONSTRAINT fk_khfall_vers FOREIGN KEY ("PSID") REFERENCES vers("PSID");

-- Each dental case (ZAHN) is associated with a person in VERS
ALTER TABLE zahnfall
ADD CONSTRAINT fk_zahnfall_vers FOREIGN KEY ("PSID") REFERENCES vers("PSID");


-- ============================================================================
-- (Green) MODULE: OUTPATIENT CASES (AMB)
-- ============================================================================

-- Primary key: each outpatient case is uniquely identified by FALLIDAMB
ALTER TABLE ambfall
ADD CONSTRAINT pk_ambfall_fallid PRIMARY KEY ("FALLIDAMB");

-- Diagnoses linked to outpatient case
ALTER TABLE ambdiag
ADD CONSTRAINT fk_ambdiag_ambfall FOREIGN KEY ("FALLIDAMB") REFERENCES ambfall("FALLIDAMB");

-- Services linked to outpatient case
ALTER TABLE ambleist
ADD CONSTRAINT fk_ambleist_ambfall FOREIGN KEY ("FALLIDAMB") REFERENCES ambfall("FALLIDAMB");

-- Procedures linked to outpatient case
ALTER TABLE ambops
ADD CONSTRAINT fk_ambops_ambfall FOREIGN KEY ("FALLIDAMB") REFERENCES ambfall("FALLIDAMB");


-- ============================================================================
-- (Yellow) MODULE: HOSPITAL CASES (KH)
-- ============================================================================

-- Primary key: each hospital case is uniquely identified by FALLIDKH
ALTER TABLE khfall
ADD CONSTRAINT pk_khfall_fallid PRIMARY KEY ("FALLIDKH");

-- Discharge info linked to hospital case
ALTER TABLE khfa
ADD CONSTRAINT fk_khfa_khfall FOREIGN KEY ("FALLIDKH") REFERENCES khfall("FALLIDKH");

-- Diagnoses linked to hospital case
ALTER TABLE khdiag
ADD CONSTRAINT fk_khdiag_khfall FOREIGN KEY ("FALLIDKH") REFERENCES khfall("FALLIDKH");

-- Procedures linked to hospital case
ALTER TABLE khproz
ADD CONSTRAINT fk_khproz_khfall FOREIGN KEY ("FALLIDKH") REFERENCES khfall("FALLIDKH");

-- Billing info linked to hospital case
ALTER TABLE khentg
ADD CONSTRAINT fk_khentg_khfall FOREIGN KEY ("FALLIDKH") REFERENCES khfall("FALLIDKH");


-- ============================================================================
-- (Red) MODULE: PRESCRIPTIONS (REZ & EZD)
-- ============================================================================

-- Primary key: each prescription uniquely identified by REZNR
ALTER TABLE rez
ADD CONSTRAINT pk_rez_reznr PRIMARY KEY ("REZNR");

-- Each prescription detail (EZD) must refer to an existing REZ entry
ALTER TABLE ezd
ADD CONSTRAINT fk_ezd_rez FOREIGN KEY ("REZNR") REFERENCES rez("REZNR");


-- ============================================================================
-- (Green) MODULE: DENTAL CARE (ZAHNFALL, ZAHNLEIST, ZAHNBEF)
-- ============================================================================

-- Primary key: each dental case is uniquely identified by FALLIDZAHN
ALTER TABLE zahnfall
ADD CONSTRAINT pk_zahnfall_fallid PRIMARY KEY ("FALLIDZAHN");

-- Dental services linked to dental case
ALTER TABLE zahnleist
ADD CONSTRAINT fk_zahnleist_zahnfall FOREIGN KEY ("FALLIDZAHN") REFERENCES zahnfall("FALLIDZAHN");

-- Dental findings linked to dental case
ALTER TABLE zahnbef
ADD CONSTRAINT fk_zahnbef_zahnfall FOREIGN KEY ("FALLIDZAHN") REFERENCES zahnfall("FALLIDZAHN");

-- ============================================================================
--  END OF CONSTRAINTS
-- ============================================================================
