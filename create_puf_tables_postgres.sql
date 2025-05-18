-- ===============================
-- PostgreSQL Schema for DM3 Data
-- ===============================

-- Table 1: Basic insurance data
CREATE TABLE "vers" (
    "VSID" BIGINT,                           -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID (encrypted)
    "GEBJAHR" SMALLINT NOT NULL,             -- Year of birth
    "PLZ" VARCHAR(5),                        -- Postal code
    "VITALSTATUS" SMALLINT NOT NULL,         -- Vital status (e.g. alive/deceased)
    "STERBEDAT" INTEGER,                     -- Date of death (8-digit code)
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model number
);

-- Table 2: Insurance quarterly status
CREATE TABLE "versq" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "VERSQ" INTEGER NOT NULL,                -- Quarter number
    "GESCHLECHT" SMALLINT NOT NULL,          -- Gender
    "VERSTAGE" INTEGER NOT NULL,             -- Total insurance days
    "VERSTAGEAUSL" INTEGER NOT NULL,         -- Insurance days abroad
    "VERSSTATUS" INTEGER NOT NULL,           -- Insurance status code
    "VERSTAGEKG" INTEGER NOT NULL,           -- Sick pay days
    "VERSTAGEKOSTERSTWAHLT" INTEGER NOT NULL,-- Optional doctor days
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 3: Disease Management Program participation
CREATE TABLE "versqdmp" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "VERSQ" INTEGER NOT NULL,                -- Quarter number
    "DMPPROG" VARCHAR(2) NOT NULL,           -- DMP program code
    "DMPTAGE" INTEGER NOT NULL,              -- Days of participation
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 4: Outpatient case master
CREATE TABLE "ambfall" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "ABRQ" INTEGER NOT NULL,                -- Billing quarter
    "FALLIDAMB" VARCHAR(11) NOT NULL,       -- Outpatient case ID
    "SVNR" VARCHAR(25),                     -- Social security number
    "SVTYP" SMALLINT,                        -- Insurance type
    "BSNRPSEUDO" BIGINT,                    -- Pseudonymized doctor ID
    "BSNRKV" SMALLINT,                       -- Doctor’s insurance code
    "BSNRUEBPSEUDO" BIGINT,                 -- Referring doctor pseudonym
    "BSNRUEBKV" SMALLINT,                    -- Referring KV code
    "LANRUEBPSEUDO" BIGINT,                 -- Referring doctor LANR pseudonym
    "LANRUEBFG" SMALLINT,                    -- Specialty code
    "LANRUEBPRUEF" VARCHAR(1),              -- Validation code
    "INANSPRARTAMB" VARCHAR(1) NOT NULL,    -- Type of outpatient visit
    "UNFALL" SMALLINT NOT NULL,             -- Accident indicator
    "BEHANDARTAMB" SMALLINT,                -- Treatment type
    "ENTBINDUNGSDAT" DATE,                  -- Delivery date (if any)
    "PUNKTZAHL" REAL,                       -- Points
    "FALLKOAMB" REAL,                       -- Case cost
    "DIALYSESACHKO" REAL,                   -- Dialysis cost
    "BEGINNDATAMB" DATE,                    -- Start date
    "ENDEDATAMB" DATE,                      -- End date
    "BJAHR" SMALLINT NOT NULL,              -- Report year
    "BNR" VARCHAR(8) NOT NULL,                 -- Company number
    "DATENMODELL" SMALLINT NOT NULL         -- Data model ID
);

-- Table 5: Outpatient diagnoses
CREATE TABLE "ambdiag" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDAMB" VARCHAR(11) NOT NULL,       -- Outpatient case ID
    "ICDAMB_CODE" VARCHAR(12) NOT NULL,     -- ICD diagnosis code
    "ICDAMB_ZUSATZ" VARCHAR(12),            -- Additional code
    "DIAGSICH" VARCHAR(1),                  -- Diagnosis certainty
    "DIAGLOKAL" VARCHAR(1),                 -- Localization
    "DIAGDAT" INTEGER,                         -- Diagnosis date
    "BJAHR" SMALLINT NOT NULL,              -- Report year
    "BNR" VARCHAR(8) NOT NULL,                 -- Company number
    "DATENMODELL" SMALLINT NOT NULL         -- Data model ID
);

-- Table 6: Outpatient services
CREATE TABLE "ambleist" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDAMB" VARCHAR(11) NOT NULL,       -- Outpatient case ID
    "NBSNRPSEUDO" BIGINT,                   -- Pseudonymized doctor billing number
    "NBSNRKV" SMALLINT,                      -- Health insurance code for doctor
    "LANRPSEUDO" BIGINT,                    -- Pseudonymized doctor LANR
    "LANRFG" SMALLINT,                       -- Doctor's specialty
    "LANRPRUEF" VARCHAR(1),                 -- Validation flag
    "GONR" VARCHAR(25),                     -- Fee schedule number
    "GONRDAT" DATE NOT NULL,                -- Service date
    "MULTIPLIKATOR" VARCHAR(80),           -- Service multiplier
    "ABRBEGR" VARCHAR(200),                -- Billing justification
    "SACHKOBEZ" VARCHAR(200),              -- Description of material costs
    "AMBLEISTZEIT" VARCHAR(4),             -- Duration/time code
    "TSVGART" BIGINT,                      -- TSVG type code
    "TSVGDAT" VARCHAR(10),                 -- TSVG date
    "TSVGARZT" VARCHAR(20),                -- TSVG doctor
    "TSVGBSNRPSEUDO" BIGINT,              -- TSVG pseudonymized billing number
    "TSVGBSNRKV" SMALLINT,                 -- TSVG billing number (KV)
    "ZWEITMEIN" VARCHAR(8),                -- Second opinion indicator
    "GONRBEWERT" NUMERIC(7,2),             -- Fee evaluation amount
    "BJAHR" SMALLINT NOT NULL,              -- Report year
    "BNR" VARCHAR(8) NOT NULL,                 -- Company number
    "DATENMODELL" SMALLINT NOT NULL         -- Data model ID
);

-- Table 7: Outpatient procedures (OPS codes)
CREATE TABLE "ambops" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDAMB" VARCHAR(11) NOT NULL,       -- Outpatient case ID
    "OPS" VARCHAR(12) NOT NULL,             -- OPS procedure code
    "OPSLOKAL" VARCHAR(1),                  -- Localization indicator
    "OPSDAT" DATE,                          -- Procedure date
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 8: Dental cases
CREATE TABLE "zahnfall" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "LEISTQ" INTEGER,                        -- Billing quarter
    "FALLIDZAHN" VARCHAR(11) NOT NULL,      -- Dental case ID
    "ZANRPSEUDO" BIGINT,                    -- Pseudonymized dentist ID
    "ZANRABRPSEUDO" BIGINT,                 -- Billing dentist pseudonym
    "ZAKZV" SMALLINT,                        -- Dental insurance association
    "BEHANDARTZAHN" VARCHAR(2),             -- Dental treatment type
    "BEGINNDATZAHN" INTEGER NOT NULL,                   -- Treatment start date
    "ENDEDATZAHN" INTEGER NOT NULL,                     -- Treatment end date
    "FALLKOZAHN" NUMERIC(12,2),             -- Dental case cost
    "EIGENLABOR" NUMERIC(12,2),             -- In-house lab costs
    "FREMDLABOR" NUMERIC(12,2),             -- External lab costs
    "INANSPRARTZAHN" VARCHAR(1),            -- Service usage type
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 9: Dental services
CREATE TABLE "zahnleist" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDZAHN" VARCHAR(11) NOT NULL,      -- Dental case ID
    "LEISTDAT" DATE,                        -- Date of service
    "ZAHN" VARCHAR(5),                      -- Tooth identifier
    "GEBNR" VARCHAR(25),                    -- Dental code
    "GEBPOS" VARCHAR(5),                    -- Position in jaw
    "GEBNRZAHL" INTEGER,                    -- Numeric dental code
    "BJAHR" INTEGER NOT NULL,                -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 10: Dental findings
CREATE TABLE "zahnbef" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDZAHN" VARCHAR(11) NOT NULL,      -- Dental case ID
    "BEFNR" VARCHAR(5),                     -- Finding number
    "ZAHN" VARCHAR(95),                     -- Tooth description
    "REFART" VARCHAR(1),                    -- Reference type
    "BEFNRZAHL" INTEGER,                    -- Numeric finding number
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 11: Prescriptions
CREATE TABLE "rez" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "REZNR" BIGINT NOT NULL,                -- Prescription number
    "PZNREZ" VARCHAR(10) NOT NULL,          -- Pharmaceutical central number
    "VODAT" DATE NOT NULL,                  -- Date of prescription
    "BSNRVOPSEUDO" BIGINT,                  -- Prescriber BSNR (pseudonymized)
    "BSNRVOVB" SMALLINT,                     -- Prescriber KV code
    "BSNRVOREGKNZ" SMALLINT,                -- Prescriber region code
    "LENRVOPSEUDO" BIGINT,                  -- Provider pseudonym
    "LENRVOFG" SMALLINT,                     -- Specialty code
    "LENRVOPRUEF" VARCHAR(1),               -- Validation flag
    "LENRVOPSEUDOARZTNR" VARCHAR(1),        -- Doctor number pseudonymized
    "ABGABEDAT" DATE NOT NULL,              -- Dispense date
    "BEGRUENDUNG" VARCHAR(1),               -- Reason code
    "VERTRAGSKZ" VARCHAR(25),               -- Contract code
    "APOPSEUDO" BIGINT NOT NULL,            -- Pharmacy pseudonym
    "APOKLASS" SMALLINT NOT NULL,           -- Pharmacy classification
    "APOREGKNZ" SMALLINT NOT NULL,          -- Pharmacy region code
    "APOPRUEF" VARCHAR(1),                  -- Validation flag
    "APOSITZ" VARCHAR(1),                   -- Pharmacy site type
    "APOTYP" VARCHAR(1),                    -- Pharmacy type
    "MENGE" INTEGER NOT NULL,               -- Quantity
    "NOCTU" VARCHAR(1),                     -- Night service indicator
    "AUTIDEM" VARCHAR(1) NOT NULL,          -- Aut-idem mark
    "WIRKSTOFFVO" VARCHAR(1),               -- Active ingredient prescription
    "AMBETRAG" REAL NOT NULL,               -- Medication cost
    "ABSCHLAEGE" REAL NOT NULL,             -- Discounts
    "ZUZAHLKZ" VARCHAR(1) NOT NULL,         -- Co-payment mark
    "ZUZAHLGES" REAL NOT NULL,              -- Total co-payment
    "ZUZAHL" REAL,                          -- Individual co-payment
    "MEHRKOSTEN" REAL,                      -- Additional costs
    "EIGENBET" REAL,                        -- Out-of-pocket cost
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 12: Prescription components
CREATE TABLE "ezd" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "REZNR" BIGINT NOT NULL,                -- Prescription number
    "PZNEZD" VARCHAR(8) NOT NULL,           -- Pharmaceutical code (EZD)
    "ZAEHLER" SMALLINT,                      -- Counter
    "EINHEIT" VARCHAR(2),                   -- Unit
    "FAKTOR" INTEGER NOT NULL,              -- Factor
    "FAKTORKENNZEICHEN" VARCHAR(2) NOT NULL,-- Factor identifier
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 13: Hospital cases
CREATE TABLE "khfall" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDKH" VARCHAR(11) NOT NULL,        -- Hospital case ID
    "KHPSEUDO" BIGINT NOT NULL,             -- Hospital pseudonym
    "KHKLASS" SMALLINT NOT NULL,            -- Hospital classification
    "KHREGKZ" SMALLINT NOT NULL,            -- Hospital region code
    "KHPRUEF" VARCHAR(1),                   -- Validation flag
    "AUFNDAT" VARCHAR(8) NOT NULL,          -- Admission date
    "AUFNGRUND" VARCHAR(4),                 -- Admission reason
    "ENTLASSGRUND" VARCHAR(3),              -- Discharge reason
    "AUFNFA" VARCHAR(4),                    -- Admitting department
    "EINWEISPSEUDO" BIGINT,                -- Referring doctor pseudonym
    "EINWEISFG" SMALLINT,                   -- Referring specialty
    "EINWEISPRUEF" VARCHAR(1),              -- Validation flag
    "VERANLASSKHPSEUDO" BIGINT,            -- Initiator pseudonym
    "VERANLASSKHKLASS" VARCHAR(2),         -- Initiator hospital class
    "VERANLASSKHREGKNZ" VARCHAR(2),        -- Initiator region code
    "VERANLASSKHPRUEF" VARCHAR(1),         -- Validation flag
    "BEATSTD" VARCHAR(4),                   -- Ventilation hours
    "VERANLASSSTELLEPSEUDO" VARCHAR(30),   -- Initiating institution pseudonym
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 14: Hospital discharges
CREATE TABLE "khfa" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDKH" VARCHAR(11) NOT NULL,        -- Hospital case ID
    "FA" VARCHAR(4) NOT NULL,               -- Department
    "ENTLASSDAT" VARCHAR(8) NOT NULL,       -- Discharge date
    "ENTLASSZEIT" VARCHAR(4),               -- Discharge time
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 15: Hospital diagnoses
CREATE TABLE "khdiag" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDKH" VARCHAR(11) NOT NULL,        -- Hospital case ID
    "DIAGART" VARCHAR(1) NOT NULL,          -- Diagnosis type
    "ICDKH_CODE" VARCHAR(9) NOT NULL,       -- ICD diagnosis code
    "ICDKH_ZUSATZ" VARCHAR(9),              -- ICD additional code
    "ICDLOKAL" VARCHAR(1),                  -- Localization code
    "SEKICD_CODE" VARCHAR(9),               -- Secondary ICD code
    "SEKICD_ZUSATZ" VARCHAR(9),             -- Secondary ICD additional code
    "SEKICDLOKAL" VARCHAR(1),               -- Secondary localization code
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 16: Hospital procedures
CREATE TABLE "khproz" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDKH" VARCHAR(11) NOT NULL,        -- Hospital case ID
    "PROZ" VARCHAR(11) NOT NULL,            -- Procedure code
    "PROZDAT" VARCHAR(8),                   -- Procedure date
    "PROZLOKAL" VARCHAR(1),                 -- Localization code
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);

-- Table 17: Hospital billing
CREATE TABLE "khentg" (
    "VSID" BIGINT,                            -- Insurance ID
    "PSID" BYTEA NOT NULL,                   -- Person ID
    "FALLIDKH" VARCHAR(11) NOT NULL,        -- Hospital case ID
    "ENTGART" VARCHAR(8) NOT NULL,          -- Type of billing
    "ENTGBETRAG" NUMERIC(12,2),            -- Billing amount
    "ABRVONDAT" VARCHAR(8),                -- Billing from date
    "ABRBISDAT" VARCHAR(8) NOT NULL,       -- Billing to date
    "ENTGZAHL" VARCHAR(3),                 -- Number of billed items
    "TAGEOBE" VARCHAR(3),                  -- Days above threshold
    "BJAHR" SMALLINT NOT NULL,               -- Report year
    "BNR" VARCHAR(8) NOT NULL,                  -- Company number
    "DATENMODELL" SMALLINT NOT NULL          -- Data model ID
);
