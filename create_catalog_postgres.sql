
/*
===============================================================================
 Project     : CORE (Data Model 3)
 File        : create_catalog_postgres.sql
 Description : Table creation and schema definitions based on standardized 
               German classification systems for diagnoses (ICD-10-GM) and 
               procedures (OPS).

 References  :
   - ICD-10-GM 2024 (International Statistical Classification of Diseases, 
     German Modification)
     Bundesinstitut für Arzneimittel und Medizinprodukte (BfArM)
     https://www.bfarm.de/SharedDocs/Downloads/DE/Kodiersysteme/klassifikationen/icd-10-gm/version2024/icd10gm2024syst-meta_zip.html

   - OPS 2025 (Operationen- und Prozedurenschlüssel)
     Bundesinstitut für Arzneimittel und Medizinprodukte (BfArM)
     https://www.bfarm.de/SharedDocs/Downloads/DE/Kodiersysteme/klassifikationen/ops/version2025/ops2025syst-meta_zip.html

 Author      : Gokul Thothathri 
 Date        : 04.06.2025
===============================================================================
*/
CREATE TABLE "icd10_catalogue" (
    "KAPITELNUMMER" VARCHAR(5),            -- e.g., 3
    "KLASSART" VARCHAR(5),                 -- e.g., N = Normal, T = Terminal
    "DIM1" VARCHAR(5),                     -- e.g., X
    "DIM2" VARCHAR(5),                     -- e.g., 1
    "DREISTELLER" VARCHAR(10),            -- e.g., A00
    "VIERSTELLER_MIT_PUNKT" VARCHAR(10),  -- e.g., A00.-
    "VIERSTELLER_OHNE_PUNKT" VARCHAR(10), -- e.g., A00
    "SCHLÜSSELNUMMER" VARCHAR(10),        -- e.g., A00
    "TITEL_LANG" TEXT,                    -- e.g., "Cholera durch Vibrio..."
    "TITEL_KURZ" TEXT,                    -- e.g., Cholera
    "HINWEIS" TEXT,                       -- usually empty
    "EXCLUDES" TEXT,                      -- usually empty
    "GESCHLECHT_1" VARCHAR(5),            -- e.g., V
    "GESCHLECHT_2" VARCHAR(5),            -- e.g., V
    "DIM1_KODE_1" VARCHAR(10),            -- e.g., 1-002
    "DIM1_KODE_2" VARCHAR(10),            -- e.g., 2-001
    "DIM1_KODE_3" VARCHAR(10),            -- e.g., 3-003
    "DIM1_KODE_4" VARCHAR(10),            -- e.g., 4-002
    "ALTER_VON" VARCHAR(5),               -- e.g., 1
    "ALTER_BIS" VARCHAR(5),               -- e.g., 9
    "ALTER_EINHEIT" VARCHAR(5),           -- e.g., 9
    "GUELTIG_VON" VARCHAR(10),            -- e.g., 9999
    "GUELTIG_BIS" VARCHAR(10),            -- e.g., 9999
    "KENNZEICHEN" VARCHAR(5),             -- e.g., 9
    "DIM2_KODE_1" VARCHAR(5),             -- e.g., J
    "DIM2_KODE_2" VARCHAR(5),             -- e.g., J
    "DIM2_KODE_3" VARCHAR(5),             -- e.g., J
    "DIM2_KODE_4" VARCHAR(5)              -- e.g., J
);

CREATE TABLE "ops_catalogue" (
    "KAPITELNUMMER" VARCHAR(5),            -- e.g., 4
    "KLASSART" VARCHAR(5),                 -- e.g., T = Terminalkategorie
    "DIM1" VARCHAR(5),                     -- Dimension 1 (optional coding structure)
    "DIM2" VARCHAR(5),                     -- Dimension 2 (optional coding structure)
    "DREISTELLER" VARCHAR(10),            -- e.g., 5-98
    "VIERSTELLER_MIT_PUNKT" VARCHAR(10),  -- e.g., 5-987.0
    "VIERSTELLER_OHNE_PUNKT" VARCHAR(10), -- e.g., 59870
    "SCHLUESSELNUMMER" VARCHAR(15),       -- e.g., 5-987.0 (full OPS code)
    "TITEL_LANG" TEXT,                    -- Full procedure description
    "TITEL_KURZ" TEXT,                    -- Shortened title
    "HINWEIS" TEXT,                       -- Additional notes (optional)
    "EXCLUDES" TEXT,                      -- Exclusion information (optional)
    "GESCHLECHT_1" VARCHAR(5),            -- Gender relevance 1 (e.g., M, W, V)
    "GESCHLECHT_2" VARCHAR(5),            -- Gender relevance 2
    "GESCHLECHT_3" VARCHAR(5)             -- Gender relevance 3
);