-- ===============================================================================
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
 Date        : 16.06.2025
===============================================================================
*/
-- Note: This script is written for Microsoft SQL Server (T-SQL). 
-- It uses NVARCHAR for Unicode compatibility and VARCHAR(MAX) as a modern replacement for deprecated TEXT data types.  
-- ===============================================================================

CREATE TABLE [icd10_catalogue] (
    [KAPITELNUMMER] NVARCHAR(5),            -- e.g., 3
    [KLASSART] NVARCHAR(5),                 -- e.g., N = Normal, T = Terminal
    [DIM1] NVARCHAR(5),                     -- e.g., X
    [DIM2] NVARCHAR(5),                     -- e.g., 1
    [DREISTELLER] NVARCHAR(10),             -- e.g., A00
    [VIERSTELLER_MIT_PUNKT] NVARCHAR(10),   -- e.g., A00.-
    [VIERSTELLER_OHNE_PUNKT] NVARCHAR(10),  -- e.g., A00
    [SCHLÜSSELNUMMER] NVARCHAR(10),         -- e.g., A00
    [TITEL_LANG] NVARCHAR(MAX),             -- e.g., "Cholera durch Vibrio..."
    [TITEL_KURZ] NVARCHAR(MAX),             -- e.g., Cholera
    [HINWEIS] NVARCHAR(MAX),                -- usually empty
    [EXCLUDES] NVARCHAR(MAX),               -- usually empty
    [GESCHLECHT_1] NVARCHAR(5),             -- e.g., V
    [GESCHLECHT_2] NVARCHAR(5),             -- e.g., V
    [DIM1_KODE_1] NVARCHAR(10),             -- e.g., 1-002
    [DIM1_KODE_2] NVARCHAR(10),             -- e.g., 2-001
    [DIM1_KODE_3] NVARCHAR(10),             -- e.g., 3-003
    [DIM1_KODE_4] NVARCHAR(10),             -- e.g., 4-002
    [ALTER_VON] NVARCHAR(5),                -- e.g., 1
    [ALTER_BIS] NVARCHAR(5),                -- e.g., 9
    [ALTER_EINHEIT] NVARCHAR(5),            -- e.g., 9
    [GUELTIG_VON] NVARCHAR(10),             -- e.g., 9999
    [GUELTIG_BIS] NVARCHAR(10),             -- e.g., 9999
    [KENNZEICHEN] NVARCHAR(5),              -- e.g., 9
    [DIM2_KODE_1] NVARCHAR(5),              -- e.g., J
    [DIM2_KODE_2] NVARCHAR(5),              -- e.g., J
    [DIM2_KODE_3] NVARCHAR(5),              -- e.g., J
    [DIM2_KODE_4] NVARCHAR(5)               -- e.g., J
);

CREATE TABLE [ops_catalogue] (
    [KAPITELNUMMER] NVARCHAR(5),            -- e.g., 4
    [KLASSART] NVARCHAR(5),                 -- e.g., T = Terminalkategorie
    [DIM1] NVARCHAR(5),                     -- Dimension 1 (optional coding structure)
    [DIM2] NVARCHAR(5),                     -- Dimension 2 (optional coding structure)
    [DREISTELLER] NVARCHAR(10),             -- e.g., 5-98
    [VIERSTELLER_MIT_PUNKT] NVARCHAR(10),   -- e.g., 5-987.0
    [VIERSTELLER_OHNE_PUNKT] NVARCHAR(10),  -- e.g., 59870
    [SCHLUESSELNUMMER] NVARCHAR(15),        -- e.g., 5-987.0 (full OPS code)
    [TITEL_LANG] NVARCHAR(MAX),             -- Full procedure description
    [TITEL_KURZ] NVARCHAR(MAX),             -- Shortened title
    [HINWEIS] NVARCHAR(MAX),                -- Additional notes (optional)
    [EXCLUDES] NVARCHAR(MAX),               -- Exclusion information (optional)
    [GESCHLECHT_1] NVARCHAR(5),             -- Gender relevance 1 (e.g., M, W, V)
    [GESCHLECHT_2] NVARCHAR(5),             -- Gender relevance 2
    [GESCHLECHT_3] NVARCHAR(5)              -- Gender relevance 3
);
