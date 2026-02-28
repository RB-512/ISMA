## ADDED Requirements

### Requirement: La page upload propose une zone de drag-and-drop
Le système SHALL afficher une zone de drop visuelle sur la page upload PDF. L'utilisateur SHALL pouvoir glisser-déposer un fichier PDF ou cliquer pour ouvrir le sélecteur de fichiers. La zone SHALL afficher un état visuel distinct (bordure colorée, icône) pendant le survol d'un fichier.

#### Scenario: Drop d'un fichier PDF
- **WHEN** l'utilisateur glisse un fichier PDF sur la zone de drop
- **THEN** la zone change d'état visuel (bordure accent, fond légèrement coloré) et le fichier est assigné à l'input file

#### Scenario: Clic sur la zone ouvre le sélecteur
- **WHEN** l'utilisateur clique sur la zone de drop
- **THEN** le sélecteur de fichiers natif s'ouvre

#### Scenario: Affichage du nom du fichier sélectionné
- **WHEN** un fichier est sélectionné (par drop ou par clic)
- **THEN** le nom du fichier et sa taille sont affichés dans la zone, avec un bouton pour retirer la sélection

#### Scenario: Fonctionnement sans JavaScript
- **WHEN** JavaScript est désactivé
- **THEN** l'input file standard est toujours visible et fonctionnel (progressive enhancement)
