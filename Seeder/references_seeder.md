# Seeder References for Synthetic HIV-PrEP Dataset (FDZ DM3)

This file lists all scientific, institutional, and epidemiological sources used in the enrichment logic of seeder scripts

---

## [1] Marcus et al. (2024)
**Citation:**  
Marcus, U., Zimmermann, R., Kollan, C., & Bremer, V. (2024). *HIV and PrEP in Germany: Characteristics of PrEP users and their HIV-related behaviors*. Archives of Sexual Behavior.  
**DOI:** https://doi.org/10.1007/s10508-024-02922-5  
**Used for:** Age distribution of PrEP users (1980–2000 birth years); urban clustering

---

## [2] Robert Koch-Institut (2024)
**Citation:**  
Robert Koch-Institut. (2024). *Schätzung der Anzahl der HIV-Neuinfektionen in den Jahren 2022 und 2023 sowie der Gesamtzahl der Menschen, die Ende 2023 mit HIV in Deutschland leben (Epidemiologisches Bulletin 28/2024)*.  
**PDF Link:** [Download PDF](https://www.rki.de/DE/Aktuelles/Publikationen/Epidemiologisches-Bulletin/2024/28_24.pdf?__blob=publicationFile&v=2)  
**Used for:** HIV prevalence and new infections by age and geography

---

## [3] Marcus et al. (2023)
**Citation:**  
Marcus, U., Kollan, C., Bremer, V., & Zimmermann, R. (2023). *HIV-Präexpositionsprophylaxe (PrEP) in Deutschland – Eine Analyse der Versorgungsdaten und Nutzungscharakteristika*. Bundesgesundheitsblatt – Gesundheitsforschung – Gesundheitsschutz, 66(10), 1081–1091.  
**DOI:** https://doi.org/10.1007/s00103-023-03733-0  
**Used for:** Age band concentration (25–45 years), GEBJAHR targeting

---

## [4] Cordioli et al. (2021)
**Citation:**  
Cordioli, M., Gios, L., Huber, J. W., et al. (2021). *Estimating the percentage of European MSM eligible for PrEP: insights from a bio-behavioural survey in thirteen cities*. Sexually Transmitted Infections, 97(7), 534–540.  
**DOI:** https://doi.org/10.1136/sextrans-2020-054788  
**Used for:** Urban clustering (Berlin, Hamburg, Cologne, etc.)

---

## [5] Klein et al. (2022)
**Citation:**  
Klein, H., Bräunig, J., Jansen, K., Funke, J., Drewes, J., & Burchard, G. D. (2022). *PrEP adherence and retention in Germany: A cohort study among men who have sex with men*. AIDS and Behavior, 26(3), 847–858.  
**DOI:** https://doi.org/10.1007/s10461-021-03537-3  
**Used for:** Mortality probability modeling (VITALSTATUS); low mortality bias among PrEP users

---

## [6] Deutscher Bundestag (2019)
**Citation:**  
Deutscher Bundestag. (2019). *Drucksache 19/11892 – PrEP-Kostenübernahme durch die gesetzliche Krankenversicherung (GKV)*.  
**Link:** https://dserver.bundestag.de/btd/19/118/1911892.pdf  
**Used for:** BJAHR limits (2019–2023) post-PrEP reimbursement legislation

---

## [7] Bundeszentrale für gesundheitliche Aufklärung (BZgA) (2023)
**Citation:**  
BZgA. (2023). *Monitoring der HIV-Präexpositionsprophylaxe (PrEP) in Deutschland: Jahresbericht 2023*. Köln: BZgA.  
**Link:** https://www.bzga.de/forschung/studien/hivundprep/  
**Used for:** GESCHLECHT distribution in `versq`, reporting year bias, urban prevalence

---

## [8] GKV-Spitzenverband (2023)
**Citation:**  
GKV-Spitzenverband. (2023). *Betriebsnummern und Vertragspartnerkennzeichen*.  
**Link:** https://www.gkv-datenaustausch.de  
**Used for:** Generating realistic BNR company codes (8-digit alphanumeric)

---

## [9] Forschungsdatenzentrum Gesundheit (2023)
**Citation:**  
Forschungsdatenzentrum Gesundheit. (2023). *Datenmodell 3: Datenstruktur und Variablenbeschreibung*. BfArM.  
**Link:** https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/  
**Used for:** Datenmodell = 3, schema structure and alignment

---

---

## [10] Spinner et al. (2018)
**Citation:**  
Spinner, C. D., Boesecke, C., Zink, A., Jessen, H., Stellbrink, H.-J., & Rockstroh, J. K. (2018).  
*HIV pre-exposure prophylaxis (PrEP): a review of current knowledge and future perspectives*.  
**Journal:** Infection, 46(4), 453–460.  
**DOI:** https://doi.org/10.1007/s15010-018-1185-5  
**Used for:**  
- Justification for assigning higher `VERSTAGE` values (180–365 days)  
- Describes quarterly monitoring, continuous physician contact, and renal testing during PrEP care

---

## [11] World Health Organization (2015)
**Citation:**  
World Health Organization. (2015).  
*Guideline on when to start antiretroviral therapy and on pre-exposure prophylaxis for HIV*.  
**Link:** https://www.who.int/publications/i/item/9789241509565  
**Used for:**  
- Supports long-term engagement in PrEP programs  
- Recommends regular, continued PrEP services and quarterly follow-up as standard care

---

## [12] Grant et al. (2010) – The iPrEx Study
**Citation:**  
Grant, R. M., Lama, J. R., Anderson, P. L., et al. (2010).  
*Preexposure chemoprophylaxis for HIV prevention in men who have sex with men*.  
**Journal:** New England Journal of Medicine, 363(27), 2587–2599.  
**DOI:** https://doi.org/10.1056/NEJMoa1011205  
**Used for:**  
- Foundational evidence for the effectiveness of PrEP under continuous monitoring  
- Monthly or quarterly check-ins imply stable, long-term health insurance use (`VERSTAGE` relevance)

---

---

## [13] GKV-Versichertenstatus Codierung (Standardstruktur)

**Citation:**  
GKV-Spitzenverband. (2022). *Leistungserbringer: Versicherungsstatus und Schlüsselverzeichnis zur Datenübermittlung nach § 295 SGB V*.  
**Link:** https://www.gkv-datenaustausch.de/media/dokumente/leistungserbringer/ambulanter_bereich/Verzeichnis_Schluesselzahlen.pdf  
**Used for:**  
- Coding scheme for `VERSSTATUS` values in health data exchange  
- Examples:  
  - `10001` → Regelfall gesetzlich Versicherter (Standard GKV)  
  - `10002` → Besonderer Versichertenstatus (z.B. nach §10 SGB V)  
  - `10003` → Ersatzkasse oder Sonderformen  
  - `99999` → Unbekannt / technisches Platzhalterfeld 

---
---

## [14] ECDC (2023)
**Citation:**  
European Centre for Disease Prevention and Control. (2023).  
*HIV prevention and care among migrants in the EU/EEA – Technical Report*.  
**Link:** https://www.ecdc.europa.eu/en/publications-data/hiv-prevention-and-care-among-migrants-europe  
**Used for:**  
- Justifies assigning non-zero `VERSTAGEAUSL` to simulate migrant and mobile PrEP users  
- Reflects care-seeking behaviors across EU countries

---

## [15] GKV-Spitzenverband – Ausland (2023)
**Citation:**  
GKV-Spitzenverband. (2023).  
*Grenzüberschreitende Gesundheitsversorgung – Informationen zur Erstattung von Behandlungskosten im Ausland*.  
**Link:** https://www.gkv-spitzenverband.de/krankenversicherung/ausland/ausland.jsp  
**Used for:**  
- Establishes legal basis for cross-border insurance coverage under German law  
- Applies to EU coordination of care and migrant support

---
