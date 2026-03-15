## ADDED Requirements

### Requirement: Conversion montant ERILIA resiliente
La methode `_convertir_montant_fr` DOIT gerer les valeurs non convertibles en Decimal sans lever d'exception. Les valeurs invalides retournent `Decimal(0)`.

#### Scenario: Valeur malformee dans le PDF
- **WHEN** pdfplumber extrait une valeur comme `"1."` ou `".."` qui match le regex mais n'est pas un Decimal valide
- **THEN** la methode retourne `Decimal(0)` et continue l'extraction des autres lignes
