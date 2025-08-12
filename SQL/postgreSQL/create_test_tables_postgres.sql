
-- For l-diversity  (DM3 SEEDER)
CREATE TABLE khdiag_qi AS
SELECT
  v."PLZ" AS "PLZ",
  v."GEBJAHR" AS "GEBJAHR",
  k."ICDKH_CODE" AS "sens"
FROM khdiag_puf k
JOIN vers_puf v ON v."VSID" = k."VSID";

-- For -delta - presence  (DM3 SEEDER)
-- latest gender per person from versq
DROP TABLE IF EXISTS vers_qi_seed_gender;
CREATE TABLE vers_qi_seed_gender AS
SELECT DISTINCT ON (q."VSID")
       q."VSID", q."GESCHLECHT"
FROM versq q
ORDER BY q."VSID", q."BJAHR" DESC, q."VERSQ" DESC;

-- presence QIs: PLZ3 + decade + gender
DROP TABLE IF EXISTS vers_qi_seed_plus;
CREATE TABLE vers_qi_seed_plus AS
SELECT
  v."VSID",
  LEFT(LPAD(COALESCE(v."PLZ",'00000'),5,'0'),3)   AS "PLZ3",
  (FLOOR(v."GEBJAHR"/10)*10)::int                 AS "GEBJAHR_BAND",
  g."GESCHLECHT"
FROM vers v
LEFT JOIN vers_qi_seed_gender g USING ("VSID");

CREATE INDEX ON vers_qi_seed_plus ("PLZ3");
CREATE INDEX ON vers_qi_seed_plus ("GEBJAHR_BAND");
CREATE INDEX ON vers_qi_seed_plus ("GESCHLECHT");
CREATE INDEX ON vers_qi_seed_plus ("VSID");

-- For -delta - presence Test  (DM3 PUF))
-- latest gender per person from versq_puf
DROP TABLE IF EXISTS vers_qi_puf_gender;
CREATE TABLE vers_qi_puf_gender AS
SELECT DISTINCT ON (q."VSID")
       q."VSID", q."GESCHLECHT"
FROM versq_puf q
ORDER BY q."VSID", q."BJAHR" DESC, q."VERSQ" DESC;

-- presence QIs: PLZ3 + decade + gender
DROP TABLE IF EXISTS vers_qi_puf_plus;
CREATE TABLE vers_qi_puf_plus AS
SELECT
  v."VSID",
  LEFT(LPAD(COALESCE(v."PLZ",'00000'),5,'0'),3)   AS "PLZ3",
  (FLOOR(v."GEBJAHR"/10)*10)::int                 AS "GEBJAHR_BAND",
  g."GESCHLECHT"
FROM vers_puf v
LEFT JOIN vers_qi_puf_gender g USING ("VSID");

CREATE INDEX ON vers_qi_puf_plus ("PLZ3");
CREATE INDEX ON vers_qi_puf_plus ("GEBJAHR_BAND");
CREATE INDEX ON vers_qi_puf_plus ("GESCHLECHT");
CREATE INDEX ON vers_qi_puf_plus ("VSID");

