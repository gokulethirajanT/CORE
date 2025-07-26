
# Seeder References for Synthetic HIV-PrEP Dataset (FDZ DM3)

This file lists all scientific, institutional, and epidemiological sources used in the enrichment logic of seeder scripts

---

## [1] Valbert et al. (2024)  
**Citation:**  
Valbert, F., Schmidt, D., Kollan, C., et al. (2024). *Routine Data Analysis of HIV Pre-Exposure Prophylaxis Use and Rates of Sexually Transmitted Infections Since Coverage of HIV Pre-Exposure Prophylaxis by the Statutory Health Insurance in Germany*. Archives of Sexual Behavior, 53, 3663–3672.  
**DOI:** https://doi.org/10.1007/s10508-024-02922-5  

**Used for:**  
Enriching `GEBJAHR` by skewing birth years toward 1977–1997.  
Table 2 reports a **mean age of 37.4 years (SD ±9.6)** among PrEP users, indicating that the majority fall within the **27–47 age range**.  
This supports assigning higher probability to birth years **1977 to 1997** when simulating the PrEP-relevant population in insurance master data (`vers`).
**Used for:**  
Enriching `PLZ` by assigning a **70% probability to urban postal codes**, based on Table 2 which shows that **~88.6% of PrEP users resided in Germany's five largest cities or their surrounding areas** (Berlin, Cologne, Munich, Hamburg, Frankfurt).  
This justifies over-representing city-level PLZ codes like `"10115"` (Berlin), `"20095"` (Hamburg), and `"80331"` (Munich) in synthetic insurance data.

---

## [2] Bremer et al. (2022)  
**Citation:**  
Bremer, V., Jansen, K., Zimmermann, R., et al. (2022). *Sexually transmitted infections in Germany—based on data from the German National Notification System and National Reference Centers (2010–2021)*. Infection, 50, 1301–1316.  
**DOI:** https://doi.org/10.1007/s15010-022-01919-3  

**Used for:**  
Providing context for `VITALSTATUS` enrichment. While this study does not report explicit HIV-related mortality rates, it documents **STI trends in Germany**, including stable notification of HIV, increasing STI diagnoses among MSM, and successful control measures.  
It supports the assumption that **PrEP and ART strategies have contributed to stabilizing HIV outcomes**, justifying a low mortality assumption (98% alive / 2% deceased) in synthetic PrEP population data.

---

## [3] Deutscher Bundestag (2019)
**Citation:**  
Deutscher Bundestag. (2019). *Drucksache 19/11892 – PrEP-Kostenübernahme durch die gesetzliche Krankenversicherung (GKV)*.  
**Link:** https://dserver.bundestag.de/btd/19/118/1911892.pdf  
**Used for:** BJAHR limits (2019–2023) post-PrEP reimbursement legislation

---

## [4] Schmidt et al. (2024)  
**Citation:**  
Schmidt, D., Duport, Y., Kollan, C., Marcus, U., Iannuzzi, S., & von Kleist, M. (2024). *Dynamics of HIV PrEP use and coverage during and after COVID-19 in Germany*. BMC Public Health, 24(1), 1691.  
**DOI:** https://doi.org/10.1186/s12889-024-19198-y  
**PubMed:** https://pubmed.ncbi.nlm.nih.gov/38918748/  

**Used for:**  
Weighting `BJAHR` based on COVID-19’s impact on PrEP uptake. The study quantifies sharp drops in PrEP access during Q2 and Q4 of 2020 and confirms recovery and growth in 2021 and beyond (26,159 users by end of 2021). These dynamics guide synthetic reporting year distributions in PrEP-enriched insurance data.

---

## [5] Forschungsdatenzentrum Gesundheit (2023)
**Citation:**  
Forschungsdatenzentrum Gesundheit. (2023). *Datenmodell 3: Datenstruktur und Variablenbeschreibung*. BfArM.  
**Link:** https://fdz-gesundheit.github.io/datensatzbeschreibung_fdz_gesundheit/  
**Used for:** Datenmodell = 3, schema structure and alignment

---

## [6] European Centre for Disease Prevention and Control (2023)  
**Citation:**  
European Centre for Disease Prevention and Control. (2023). *Monitoring of HIV pre-exposure prophylaxis (PrEP) in the EU/EEA and the UK – Technical guidance and indicator metadata.* Stockholm: ECDC.  
**URL:** https://www.ecdc.europa.eu/assets/hiv-monitoring-preexposure/prep-monitoring-tool.html  

**Used for:**  
Ensuring uniqueness of `PSID` (pseudonymized person identifier) in the `vers` table to avoid duplicate individuals in synthetic PrEP cohorts. This is necessary for accurate calculation of longitudinal indicators such as initiation, continuation, and coverage across reporting periods.

**Relevant lines:**  
> "Each person should only be counted once, even if they receive PrEP in multiple settings or during multiple periods."  
>  
> "Avoiding duplication of records across time and facilities is critical for estimating coverage and tracking continuation."

---

## [7] ECDC (2023)
**Citation:**  
European Centre for Disease Prevention and Control. (2023).  
*HIV prevention and care among migrants in the EU/EEA – Technical Report*.  
**Link:** https://www.ecdc.europa.eu/sites/default/files/documents/hiv-migrants-dublin-declaration-november-2024.pdf  
**Used for:**  
- Justifies assigning non-zero `VERSTAGEAUSL` to simulate migrant (15% approximation ) and mobile PrEP users  
- Reflects care-seeking behaviors across EU countries

---

## [8] Insurance Status Code Source Germany

The 5-digit `Versichertenstatus` used in the `versq` table follows the structure defined by GKV-Spitzenverband:

> **Schlüsselbezeichnung:** Versichertenstatus  
> **Schlüsselgröße:** 5 Stellen  
> **1. Stelle:** 1 = Mitglieder (insured member)  
> **5. Stelle:** 1 = West, 4 = Sozialhilfeempfänger (§264 SGB V), 9 = Ost  
> — Source: *https://www.gkv-datenaustausch.de/media/dokumente/leistungserbringer_1/sonstige_leistungserbringer/technische_anlagen_archiv_4/Anlage_3_TP5_V14_20200610.pdf, GKV-Spitzenverband, p.5   

These codes are formatted as `1XXXX` and padded with zeroes to comply with machine-readable insurance card formats.  
They are used in your synthetic data generation script to reflect real-world insurance demographics.

---

## [9] Müllerschön J., Koschollek C., Santos-Hövener C., et al. (2019).
> "Impact of health insurance status among migrants from sub-Saharan Africa on access to health care and HIV testing in Germany: a participatory cross-sectional survey." 
**Link:** https://bmcinthealthhumrights.biomedcentral.com/articles/10.1186/s12914-019-0189-3
