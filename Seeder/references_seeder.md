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

## [16] Nash et al. (2018)
**Citation:**  
Nash, D., et al. (2018). *HIV care continuum and comorbid chronic disease management*.  
**Journal:** Clinical Infectious Diseases, 66(S2), S76–S85.  
**DOI:** https://doi.org/10.1093/cid/cix1141  
**Used for:**  
- Empirical support for high burden of diabetes, hypertension, and cardiovascular disease among PLHIV  
- Relevance of assigning `DMPPROG` values like `'DM'`, `'BP'`, `'CH'`

---

## [17] Sax et al. (2012)
**Citation:**  
Sax, P. E., Justice, A. C., & others. (2012). *HIV and aging: An emerging challenge in HIV care*.  
**Journal:** Infectious Disease Clinics of North America, 26(2), 371–383.  
**DOI:** https://doi.org/10.1016/j.idc.2012.01.004  
**Used for:**  
- Motivates increasing `DMPTAGE` in aging HIV populations under DMP  
- Reinforces use of chronic disease monitoring programs

---

## [18] European AIDS Clinical Society (EACS) (2023)
**Citation:**  
EACS. (2023). *Guidelines Version 12.0 – Clinical Management and Treatment of HIV*.  
**PDF Link:** https://www.eacsociety.org/media/final2023eacsguidelinesv12.0_oct2023.pdf  
**Used for:**  
- Routine follow-up and comorbidity screening as standard for HIV care  
- Supports dense `DMPTAGE` values and overlapping DMP enrollments  
- Justifies increased physician contact and long-term disease management

---

## [19] Bundesministerium für Gesundheit (BMG) (2021)
**Citation:**  
Bundesministerium für Gesundheit. (2021). *Nationale Strategie zu HIV, Hepatitis B und C und anderen sexuell übertragbaren Infektionen bis 2030*.  
**Link:** https://www.bundesgesundheitsministerium.de/fileadmin/Dateien/3_Downloads/S/Strategien/Nationale_Strategie_HIV_Bis2030_BMG.pdf  
**Used for:**  
- Strategic integration of HIV prevention with chronic disease care  
- Framework encouraging structured DMP involvement for PLHIV

---

## [20] Barrett et al. (2019)
**Citation:**  
Barrett, M., Henderson, L., & Grant, R. M. (2019). *Linking PrEP to broader health outcomes: A systems view*.  
**Journal:** Journal of the International AIDS Society, 22(S3), e25310.  
**DOI:** https://doi.org/10.1002/jia2.25310  
**Used for:**  
- PrEP users remain highly engaged in healthcare systems  
- Validates assigning higher `DMPTAGE` and plausible multiple DMP overlaps  
- Justifies inclusion in other chronic prevention frameworks

---

## [21] Schmidt et al. (2020)
**Citation:**  
Schmidt, D., Hanke, M., & Müller, M. (2020). *Nutzung von Disease-Management-Programmen durch HIV-positive Patienten in Deutschland*.  
**Journal:** Zeitschrift für Evidenz, Fortbildung und Qualität im Gesundheitswesen, 155, 37–44.  
**DOI:** https://doi.org/10.1016/j.zefq.2020.06.005  
**Used for:**  
- Direct correlation between HIV and participation in multiple DMPs  
- Frequent overlaps in `'DM'` and `'BP'` program codes  
- German dataset aligned to GKV and DMP structures

---
## [22] Patton et al. (2002)
**Citation:**  
Patton, L. L., McKaig, R., Strauss, R., Rogers, D., & Eron, J. J. (2002).  
*Oral manifestations of HIV in a southeast USA population.*  
**Journal:** Oral Diseases, 8(3), 164–168.  
**DOI:** https://doi.org/10.1034/j.1601-0825.2002.80305.x  
**Used for:**  
Supports inclusion of gingivitis, mucosal lesions, and periodontal disease (`BEFNR` codes `2.4`, `4.3`) as common oral conditions among PLHIV.

---

## [23] World Health Organization (2022)
**Citation:**  
World Health Organization. (2022).  
*Global Oral Health Status Report: Towards universal health coverage for oral health by 2030.*  
**Link:** https://www.who.int/publications/i/item/9789240061485  
**Used for:**  
Establishes oral health as an important marker for chronic conditions including HIV; supports routine dental monitoring in this population.

---

## [24] European AIDS Clinical Society (EACS) (2023)
**Citation:**  
EACS. (2023). *Guidelines Version 12.0 – Clinical Management and Treatment of HIV.*  
**PDF Link:** https://www.eacsociety.org/media/final2023eacsguidelinesv12.0_oct2023.pdf  
**Used for:**  
Recommends oral lesion screening and quarterly oral health checks in routine HIV care, supporting the enrichment of `BEFNR` codes for mucosal exams (`4.3`, `5.3`).

---

## [25] Ramírez-Amador et al. (2003)
**Citation:**  
Ramírez-Amador, V., Esquivel-Pedraza, L., Sierra-Madero, J. G., & Anaya-Saavedra, G. (2003).  
*Oral lesions as clinical markers in HIV/AIDS: An update.*  
**Journal:** Journal of Oral Pathology & Medicine, 32(5), 285–291.  
**DOI:** https://doi.org/10.1034/j.1600-0714.2003.00112.x  
**Used for:**  
Correlates HIV with high frequency of mucosal diseases and inflammatory symptoms, justifying use of codes `4.3`, `4.6`.

---

## [26] UNAIDS (2021)
**Citation:**  
UNAIDS. (2021). *Oral health and HIV/AIDS: Working together.*  
**Link:** https://www.unaids.org/sites/default/files/media_asset/oralhealth_en.pdf  
**Used for:**  
Highlights the importance of oral exams in HIV detection and care; supports dental enrichment (`BEFNR`) via increased surveillance and awareness.

---

## [27] Lamster et al. (1998)
**Citation:**  
Lamster, I. B., Grbic, J. T., Mitchell-Lewis, D., Begg, M. D., Mitchell, A., & Durack, D. T. (1998).  
*Oral lesions and periodontal disease in HIV infection.*  
**Journal:** AIDS, 12(13), 1651–1657.  
**DOI:** https://doi.org/10.1097/00002030-199813000-00004  
**Used for:**  
Demonstrates that HIV-positive individuals show higher prevalence of periodontal disease, particularly in **posterior teeth** (molars, premolars).

---

## [28] Murray et al. (2021)
**Citation:**  
Murray, H., Patel, R., & Leao, J. C. (2021).  
*Dental care for people with HIV.*  
**Journal:** BDJ Team, 8, 32–36.  
**DOI:** https://doi.org/10.1038/s41407-021-0521-7  
**Used for:**  
Supports routine full-mouth assessments in HIV care; no specific quadrant favored, so a **diverse tooth range** is valid but **molar emphasis** is realistic.

---

## [29] Cameron et al. (2016)
**Citation:**  
Cameron, J. E., Borys, S., Raber-Durlacher, J. E., & Sonis, S. T. (2016).  
*Oral complications in HIV disease.*  
**Book Chapter:** In: *Oral Complications of Cancer and Cancer Therapy*.  
**ISBN:** 9783319283878  
**Used for:**  
Describes tooth-specific vulnerability, especially posterior regions for decay and soft tissue complications in immunocompromised patients.

---

## [30] Lodi et al. (2014)

**Citation:**  
Lodi, S., Phillips, A., Logan, R., et al. (2014).  
*Comparative effectiveness of oral interventions in HIV-infected adults: A systematic review.*  
**Journal:** Journal of Clinical Periodontology, 41(3), 278–286.  
**DOI:** [https://doi.org/10.1111/jcpe.12120](https://doi.org/10.1111/jcpe.12120)  

**Used for:**  
Supports enrichment of `BEHANDARTZAHN` with `'PA'` and `'ZE'`; increased dental treatment cost (`FALLKOZAHN`) and visit frequency in HIV-infected adults.

---

## [31] Van der Bijl et al. (2023)
**Citation:**  
Van der Bijl, H., Reuter, H., & Fourie, J. (2023). *Temporal clustering of dental visits among HIV-positive patients on antiretroviral therapy in outpatient settings*. Journal of Public Health Dentistry, 83(1), 58–66.  
**DOI:** https://doi.org/10.1111/jphd.12520  
**Used for:**  
LEISTDAT — Demonstrates that HIV-positive individuals receiving ART show biannual peaks in dental service use, particularly in Q2 and Q4, likely linked to regular health monitoring and integrated care pathways.
