# Knowledge Sources and Citation Policy

## Policy

1. Every factual claim in the knowledge files should have a reliable source. Prefer primary literature, standard textbooks and authoritative databases.
2. Do not invent a DOI, page number, CAS number, SMILES or InChIKey. If a source is uncertain, mark it "verify" rather than presenting it as fact.
3. For chemical identity, use PubChem or the paper's SI; for physical data, use NIST or the paper; for methods, use the original method paper or a textbook.
4. When the knowledge base and a paper disagree, the paper's measured value wins for that paper. The knowledge base is for interpretation, not for overriding data.
5. When adding a new source, record author, year, title, journal/book and (if available) DOI. Do not paste a citation from memory without checking.

## Core textbooks and reviews

- Kohl, A. L., & Nielsen, R. B. *Gas Purification*, 5th ed. Gulf Publishing, 1997.
- Rochelle, G. T. "Amine scrubbing for CO2 capture." *Science* 325 (2009): 1652–1654.
- Wilcox, J. *Carbon Capture*. Springer, 2012.
- Theo, W. L., Lim, J. S., Hashim, H., Mustaffa, A. A., & Ho, W. S. "Review of pre-combustion capture and ionic liquid in carbon capture and storage." *Applied Energy* 183 (2016): 1633–1663. (Review; use for context, not data.)

## Equilibrium and thermodynamic models

- Kent, R. L., & Eisenberg, B. "Better data for amine treating." *Hydrocarbon Processing* 55 (1976): 87–90.
- Deshmukh, R. D., & Mather, A. E. "A mathematical model for equilibrium solubility of hydrogen sulfide and carbon dioxide in aqueous alkanolamine solutions." *Chemical Engineering Science* 36 (1981): 355–362.
- Chen, C. C., & Evans, L. B. "A local composition model for the excess Gibbs energy of aqueous electrolyte systems." *AIChE Journal* 32 (1986): 444–454.
- Austgen, D. M., Rochelle, G. T., Peng, X., & Chen, C. C. "Model of vapor-liquid equilibria for aqueous acid gas-alkanolamine systems using the electrolyte-NRTL equation." *Industrial & Engineering Chemistry Research* 28 (1989): 1060–1073.
- Pitzer, K. S. "Thermodynamics of electrolytes. I. Theoretical basis and general equations." *Journal of Physical Chemistry* 77 (1973): 268–277.
- Weiland, R. H., Chakravarti, S., & Mather, A. E. "Solubility of CO2 and H2S in aqueous alkanolamine solutions." GPA Research Report RR-155, 1993.

## MEA, PZ, AMP and blends

- Jou, F.-Y., Mather, A. E., & Otto, F. D. "The solubility of CO2 in a 30 mass percent monoethanolamine solution." *Canadian Journal of Chemical Engineering* 73 (1995): 140–147.
- Bishnoi, S., & Rochelle, G. T. "Absorption of carbon dioxide into aqueous piperazine: reaction kinetics, mass transfer and solubility." *Chemical Engineering Science* 55 (2000): 5531–5543.
- Dang, H., & Rochelle, G. T. "CO2 absorption rate and solubility in monoethanolamine/piperazine/water." *Separation Science and Technology* 38 (2003): 337–357.

## Databases and identity

- PubChem (CAS, molecular formula, molecular weight, SMILES, InChIKey): https://pubchem.ncbi.nlm.nih.gov/
- NIST Chemistry WebBook (thermophysical properties): https://webbook.nist.gov/
- Crossref/DOI resolution for bibliographic metadata: https://doi.org/
- Unpaywall for legal OA locations: https://unpaywall.org/

## Project-specific sources

- `AGENTS.md` — research boundary, QC rules, VLE and concentration red lines.
- `SOP.md` — operational workflow.
- `scripts/schema.sql` — field definitions.
- `data/compound_whitelist.csv` — current four amines and their identities.
- `README`-like manual (`碳捕集Agent使用手册.pdf`) — user-facing workflow.

## How to add a source

1. Verify the citation against the publisher/DOI/Crossref.
2. Add it under the correct topic.
3. If it supports a specific rule, add a one-line note next to the rule.
4. If it is uncertain, mark it "verify" and do not use it as a hard rule.
