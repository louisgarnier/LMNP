# Gestion locative et fiscalité — exigences à valider

Date : 27 octobre 2026. Statut : périmètre et checklist validés par le propriétaire le 27 octobre 2026 ; maquettes autorisées, avec préservation explicite des fonctionnalités existantes.

Ce document rassemble les décisions de la conversation et les exemples de champs montrés dans les captures Matera. Les captures servent de référence fonctionnelle ; elles ne prescrivent ni une copie de l'interface ni une intégration à Matera. Les données personnelles des exemples ne sont pas reproduites ici.

## 1. Objectif et méthode

Faire évoluer l'application existante vers une webapp de gestion immobilière pour propriétaires. Chaque bien dispose de sa gestion locative ; Transactions et Fiscalité restent accessibles, avec une navigation entièrement repensée et simple.

Ordre convenu : questions et exigences → validation du périmètre et de la liste hiérarchique des tâches → maquettes → prototype HTML navigable → implémentation et vérifications. Suivre l’AGENTS.md fourni par l’utilisateur et le skill tracking-project-progress : le fichier `codex-progress.html`, à la racine, est la liste de tâches de référence pour suivre les pourcentages, temps mesurés, décisions, problèmes et prochaines actions. Le maintenir à jour pendant toute l’exécution. Après approbation du périmètre, les décisions techniques et vérifications nécessaires n’exigent pas de nouvelles approbations de routine. Les validations des maquettes et du prototype restent les étapes de conception demandées. Aucun développement fonctionnel n’est autorisé par la seule rédaction de ce document. Les modèles de contrats et de dossier candidat seront fournis au moment utile.

La version actuelle de référence est sur `main`. Conserver les données et les fonctionnalités existantes pendant l'évolution. La branche locale `gestion` a été créée à la demande du propriétaire à partir de `main`. Les modifications de cadrage sont conservées sur cette branche. Sa création ne déclenche pas de publication sur GitHub.

## 2. Comptes et accès — V1

- Webapp dans le navigateur, comme l'application actuelle.
- V1 : entrée par simple saisie de l’adresse e-mail, sans code, mot de passe ni confirmation par e-mail.
- V2 : ajout de la confirmation par code reçu par e-mail.
- En V1, l’adresse saisie est un identifiant déclaré, pas une identité vérifiée. Le cloisonnement des données par propriétaire reste requis ; l’accès à un service public contenant de vraies données devra être cadré avant déploiement, sans présenter cette saisie comme une authentification sécurisée.
- Chaque propriétaire a un espace privé, sans partage entre propriétaires indépendants.
- Les biens, personnes, fichiers, transactions et calculs d'un propriétaire ne sont pas accessibles aux autres propriétaires.
- Aucun compte ni portail pour les locataires en V1.
- Réglages du compte et accès à la connexion bancaire Enable Banking déjà existante dans l’application : réutiliser son fonctionnement, sans la reconstruire.
- Fiches partenaires et interventions gérées par le propriétaire en V1. Connexion et espace partenaire reportés en V2.
- Hébergement, modalités d'inscription et service d’envoi des e-mails restent à définir ; les codes de confirmation relèvent de la V2 ; la demande de webapp ne vaut pas choix d'un hébergeur ni autorisation de déploiement.

## 3. Organisation de l'application

La navigation sera décidée dans les maquettes. Elle doit permettre :

- une vue de l'ensemble des biens du propriétaire ;
- un accès rapide à la fiche du bien, ses locataires, contrats, candidatures, documents et soldes ;
- l’accès aux transactions existantes ; arbitrer dans les maquettes entre leur emplacement actuel et un module Transactions autonome, sans dupliquer les données ni changer leur traitement ;
- l’accès à la fiscalité globale et par bien déjà existante : conserver les écrans, fonctions et calculs construits ;
- un passage simple entre gestion locative et fiscalité, sans perdre le contexte du bien ;
- une distinction explicite entre paramètres du compte, paramètres du bien et paramètres du bail.

Il s’agit d’une refonte de la navigation et de l’ajout de gestion locative. La fiscalité et les traitements comptables existants restent inchangés. L’étude porte notamment sur la manière de lier les transactions existantes aux biens, locataires et interventions côté gestion, sans seconde comptabilité parallèle.

## 4. Biens et modes de location

### 4.1 Fiche du bien

Les champs suivants proviennent des besoins et captures. Ils constituent le catalogue de départ ; les champs obligatoires, facultatifs et conditionnels seront précisés lors de la conception des formulaires.

| Bloc | Informations et pièces |
|---|---|
| Identité | Intitulé, adresse, type, étage, surface, nombre de pièces et de chambres |
| Compléments | Accès à l'immeuble, chauffage, eau chaude, présence d'une chaudière |
| Diagnostics | DPE, GES, rapports et dates ; plomb, amiante, électricité, gaz, état des risques et pollutions |
| Acquisition et finances | Date et prix d'acquisition, prêt, régime fiscal, références fiscales/SIRET pertinentes, preuve de propriété, taxe foncière, CFE et justificatifs |
| Assurances | PNO, assurance emprunteur, contrats/attestations et dates |
| Immeuble et syndic | Construction, type d'habitat, régime juridique, nom et coordonnées du syndic/gestionnaire |
| Annonces | Descriptions réutilisables, photos, informations nécessaires à la mise en location |
| Prestataires | Coordonnées, type de prestation, interventions, factures et liens vers Transactions |

Les informations et documents sont saisis/déposés manuellement. Aucun import initial Excel/CSV de biens ou locataires ni extraction automatique de documents en V1. L'import bancaire existant reste conservé.

Aucun rappel automatique d'échéance de document en V1. Les dates peuvent être conservées sans déclencher de notification.

### 4.2 Modes de location

Le mode se définit au niveau du bien :

1. Logement entier.
2. Colocation avec bail commun : plusieurs locataires sur le contrat, sans attribution de chambre par personne.
3. Location par chambre avec baux individuels : chambres définies dans le bien et chaque bail rattaché à une chambre.
4. Courte durée : périmètre limité décrit ci-dessous.

Un bien peut changer de mode dans le temps. Conserver les contrats, occupations et documents passés ; un changement ne réécrit pas les anciens baux.

### 4.3 Airbnb / Booking

Uniquement les informations du gestionnaire et de la personne chargée du ménage. Pas de réservation, synchronisation de calendrier ni gestion opérationnelle des séjours en V1.

## 5. Fiscalité et banque existantes

### 5.1 Fiscalité existante : périmètre protégé

Correction explicite du propriétaire : ce module existe déjà et ne doit pas être modifié dans ce chantier.

- Conserver les calculs, agrégations, règles, données, fonctionnalités et écrans fiscaux déjà construits.
- Ajouter le paramètre par bien « LMNP au réel / autre régime / SCI » : seuls les biens LMNP au réel alimentent la comptabilité et la fiscalité LMNP existantes. Les autres biens conservent leur gestion et leurs transactions. Aucun moteur SCI supplémentaire en V1.
- Préserver les règles de calcul existantes ; avec tous les biens au réel, les résultats doivent rester identiques à la référence. Le filtrage du périmètre est un ajout demandé, distinct d’une réécriture des calculs.
- Conserver le contexte du bien dans la navigation. Définir avant implémentation le traitement historique d’un changement de régime, sans modifier rétroactivement les résultats par hypothèse.
- Étudier le positionnement de Transactions (emplacement actuel ou module autonome) et les liens nécessaires avec la gestion par bien.
- Tout besoin technique de protection d’accès par propriétaire doit être conçu autour de l’existant, sans changer sa logique métier. Une incompatibilité avec la contrainte de préservation doit être signalée avant modification.
- Vérifier la non-régression des résultats fiscaux sur les données de référence.

### 5.2 Connexion bancaire

- Réutiliser Enable Banking et les transactions du module Finance existant.
- Ne pas créer de seconde connexion ni dupliquer les mouvements pour les loyers.
- V1 : un compte bancaire par appartement, conformément au fonctionnement actuel.
- Un compte partagé entre plusieurs appartements est reporté à une version ultérieure.
- Le propriétaire attribue manuellement les paiements aux locataires ; aucun rapprochement locataire automatique en V1.

## 6. Locataires, contrats et garanties

- Fiche locataire : identité, coordonnées, dossier et documents ; conservation de l'historique.
- Contrat distinct de la personne : un bail peut concerner plusieurs locataires.
- Contrats actuels et passés consultables.
- Informations du bail : type, dates, durée, renouvellement, loyer hors charges, charges, échéance de paiement, modalités, dépôt de garantie, révision et référence d'indice, documents d'entrée et de sortie.
- Assurance habitation : attestation et dates, sans rappels automatiques en V1.
- Garants : personne physique ou organisme tel que Visale, coordonnées/références, acte ou contrat de garantie ; rattachement au locataire/bail pertinent.
- Saisie initiale manuelle des locations existantes avec solde de départ daté par locataire : dette, crédit ou zéro, sans reprise obligatoire de tous les mouvements passés.

## 7. Loyers et suivi des paiements

### 7.1 Tableau annuel

- Sélection de l'année, locataires en lignes et mois en colonnes.
- Accès aux montants dus, paiements affectés et solde restant pour chaque mois.
- Gestion des paiements partiels et rattrapages : plusieurs paiements pour un mois, ou un paiement réparti entre plusieurs mois.
- Solde courant par locataire et identification des retards/trop-perçus.
- La somme des affectations ne doit pas dépasser le montant disponible d'un paiement.
- Règles de répartition entre personnes sur un bail commun à préciser : ne pas multiplier le loyer du bail par le nombre de signataires.
- Dépôt de garantie identifiable séparément du paiement du loyer.

### 7.2 Appels de loyer, quittances et relances

| Action | Comportement V1 |
|---|---|
| Appel de loyer | Document généré ; date d'envoi réglable par bail ; choix automatique ou manuel |
| Quittance | Document disponible et conservé ; envoi à la demande, sans envoi automatique |
| Relance d'impayé | Déclenchée manuellement par le propriétaire |
| Canal locataire | E-mail uniquement, hors échanges candidats via les plateformes |

Prévoir l'état des envois et la visibilité des erreurs, afin qu'une opération ne soit pas présentée comme envoyée lorsqu'elle a échoué. Les règles exactes de génération des documents, modèles et périodes couvertes seront définies avec les formulaires.

## 8. Révision du loyer et régularisation des charges

### 8.1 Révision du loyer

Module dédié : calcul proposé à partir des données du bail, détail consultable, validation du propriétaire avant application, puis e-mail explicatif au locataire. La formule, les indices et les règles d'application restent à spécifier et vérifier avant développement.

### 8.2 Régularisation des charges

Décisions exprimées :

- Module dans lequel le propriétaire définit les charges qu'il a payées et leurs montants annuels pour la colocation.
- Répartition entre les locataires présents, en tenant compte de leurs dates d'entrée et de sortie.
- Convention de prorata retenue : 30/360, mois de 30 jours et année de 360 jours.
- La part d'une chambre vide est répartie entre les locataires présents ; ce n'est donc pas une division fixe par le nombre de chambres toute l'année.
- Sans aucun locataire présent, les charges de la période restent au propriétaire.
- Comparaison de la part calculée pour chaque locataire avec ses provisions effectivement versées sur la période, sans confondre provisions attendues et payées.
- Résultat détaillé : complément à demander ou montant à restituer.
- Validation obligatoire par le propriétaire avant application et envoi de l'e-mail explicatif.

Points de calcul à préciser : périodes couvertes par chaque charge, dépenses répartissables selon le bail, variante exacte de 30/360 pour fins de mois/février, inclusion des dates de frontière, arrondis et conservation du total réparti. Le comportement souhaité ci-dessus n'est pas une validation juridique de son applicabilité à tous les baux ; la spécification du calcul devra être cohérente avec les contrats concernés. Aucun calcul légal ou fiscal nouveau n'est certifié par ce document.

## 9. Annonces et candidatures

### 9.1 Plateformes et contenus

- Leboncoin et La Carte des Colocs sont les deux plateformes cibles V1.
- Centraliser les photos, descriptions et données pour publier ou réactiver rapidement une annonce, notamment lors de la libération d'une chambre.
- Rattacher annonces, échanges et candidatures au bon bien/chambre. Le titre aide à l'identification, mais ne doit pas être supposé unique.
- Objectif : récupérer les messages et automatiser les réponses/demandes selon un workflow défini.
- Faisabilité de publication, réactivation, lecture et envoi de messages à vérifier séparément pour chaque plateforme. Aucune disponibilité d'API ou automatisation complète n'est acquise à ce stade.
- Si une intégration ne permet pas le résultat demandé, présenter la limite et faire valider l'alternative avant de réduire le périmètre.

### 9.2 Règle fondamentale du kanban

**Chaque changement d'étape exige une validation du propriétaire.** La réception d'un message ou d'une pièce peut mettre à jour le dossier, mais ne fait pas passer automatiquement à l'étape suivante.

Les messages et demandes peuvent partir automatiquement après validation de l'étape, suivant les règles prévues. Les destinataires, déclencheurs, modèles et conditions exactes seront définis dans le workflow détaillé avant activation.

### 9.3 Parcours précisé par le propriétaire

La numérotation ci-dessous remet en ordre les étapes fournies, sans transformer la réception de pièces en validation automatique. Chaque passage reste validé par le propriétaire.

**Entrée dans le parcours :** création manuelle d’un contact ou récupération depuis Leboncoin / La Carte des Colocs, puis rattachement à l’annonce et au bien/chambre concernés.

1. **Envoi du message initial.** Collecter :
   - nom et prénom ;
   - âge ;
   - e-mail et téléphone ;
   - situation : étudiant (année d’étude) ou professionnel ;
   - garantie Visale ou garant physique ;
   - date d’entrée souhaitée ;
   - durée envisagée de location.
2. **Validation initiale par le propriétaire.** Vérifier les réponses avant de demander les pièces.
3. **Demande et collecte des pièces.** Liste fournie :
   - garantie Visale ;
   - bulletins de paie des trois derniers mois ;
   - justificatif de situation professionnelle ;
   - avis d’imposition ;
   - attestation habitation actuelle ;
   - pièce d’identité.
4. **Validation des informations et des pièces par le propriétaire.** Un dossier incomplet ne doit pas être considéré complet simplement parce qu’un fichier est présent.
5. **Visite prévue.** Suivi du statut de visite ; voir la règle parallèle ci-dessous.
6. **Validation de la visite.** Case « Visite effectuée » validée par le propriétaire.
7. **Création du dossier.** Générer un PDF récapitulatif regroupant les informations validées et les pièces jointes. Le propriétaire fournira un exemple au moment utile.
8. **Emménagement.** Sous-tâches :
   - demande de paiement du dépôt de garantie et du premier loyer, puis confirmation de leur réception ;
   - demande de l’assurance habitation du nouveau logement, puis réception de l’attestation ;
   - établissement du contrat à partir du modèle et des variables ;
   - signature du contrat ;
   - prise de rendez-vous pour l’état des lieux et l’emménagement, puis confirmation de l’état des lieux d’entrée effectué ;
   - validation finale et transformation en locataire actuel.

Les demandes de paiement ou de document ne valent pas réception. L’attestation du logement actuel, demandée au dossier, est distincte de l’assurance du nouveau logement exigée à l’entrée.

La liste des pièces devra être adaptée à la situation déclarée et au type de garant : notamment les cas étudiant sans salaire, garant physique et absence d’assurance actuelle. Les variantes, pièces du garant et règles applicables seront précisées avant activation des demandes ; aucune règle automatique de rejet n’est définie ici.

### 9.4 Visite et rendez-vous

- Conserver la décision précédente : la visite est suivie en parallèle et ne bloque pas la collecte ni la validation des informations du dossier.
- Le parcours transmis place la génération du PDF récapitulatif après validation de la visite ; la préparation de son contenu peut avancer avant.
- Case « Visite effectuée » obligatoire avant création du bail.
- Les mentions « Visite prévue » et « Prise de rendez-vous état des lieux / emménagement » ajoutent un suivi manuel des rendez-vous convenus dans le parcours V1.
- Le choix automatisé de créneaux, la réservation par le candidat et la synchronisation de calendriers restent en V2.
- L’ordre opérationnel des sous-tâches d’emménagement sera rendu explicite dans les maquettes, sans confondre demande, réalisation et validation.

### 9.5 Conditions de la dernière étape

Toutes les conditions doivent être confirmées : bail signé, attestation d'assurance habitation reçue, dépôt de garantie payé, premier loyer payé, état des lieux d'entrée effectué. La simple génération d'un document ou demande de paiement ne satisfait pas ces conditions.

## 10. Baux, signature, états des lieux et prestataires

- Formulaire de variables à partir de modèles de bail fournis par le propriétaire du projet.
- Préremplissage depuis le bien et les informations des nouveaux locataires, puis vérification des valeurs.
- Génération du bail PDF et conservation du document final.
- Signature électronique via un prestataire à sélectionner : comparer coût et niveau de signature approprié, sans retenir d'office DocuSign ou Yousign.
- Statut de signature consultable et document signé rattaché au contrat.
- États des lieux d'entrée et de sortie : document généré à remplir manuellement, ou dépôt du rapport établi par un prestataire.
- Fiche et intervention du prestataire liées au bien, au rapport, à la facture et à la transaction correspondante dans Finance.
- En V1, ces informations sont renseignées par le propriétaire. L'espace prestataire est en V2.

## 11. Sortie du locataire

- Saisie et validation manuelles du préavis et de la date de départ par le propriétaire.
- Conservation de la date de réception et de la pièce de préavis.
- Checklist de sortie : organisation/réalisation de l'état des lieux, dépôt du rapport, suivi de la restitution du dépôt de garantie et clôture.
- Conservation du locataire, du bail, des documents et des soldes historiques après la sortie.
- Les règles de retenue, de solde de sortie et de clôture restent à détailler ; pas de restitution bancaire automatique demandée.

## 12. V2 / ultérieur

- Confirmation de connexion par code reçu par e-mail.

- Comptes et espace prestataire : accès aux seules colocations autorisées, consultation et saisie des prestations réalisées. Droits détaillés à concevoir plus tard.
- Comptabilité SCI et autres moteurs fiscaux.
- Compte bancaire commun à plusieurs appartements et affectation des opérations entre biens.
- Relances automatiques d'impayés.
- Rappels d'échéance des documents.
- Planification des visites et choix de créneaux.

Non demandés en V1, sans engagement automatique de livraison ultérieure : portail locataire, OCR/extraction documentaire, import initial de biens/locataires, SMS/WhatsApp, gestion des réservations et opérations de courte durée.

## 13. Critères d'acceptation du périmètre proposé

1. Un propriétaire entre son adresse e-mail sans confirmation en V1 ; les données sont rattachées à son espace. La vérification de l’adresse relève de la V2 et aucune sécurité d’identité vérifiée n’est revendiquée en V1.
2. Il crée manuellement un bien, ses informations/documents et son mode de location ; un changement de mode conserve l'historique.
3. Les règles de calcul et fonctionnalités fiscales existantes sont conservées ; avec tous les biens au réel, les résultats restent identiques sur les données de référence. Le paramètre par bien exclut les autres régimes et SCI du périmètre LMNP. Le nouvel accès et les liens avec la gestion ne créent ni duplication ni modification comptable.
4. Le suivi locatif utilise les transactions déjà importées par Finance sans les dupliquer.
5. Le tableau annuel reflète correctement un solde initial, des paiements partiels et des affectations sur plusieurs mois.
6. Appels de loyer automatiques ou manuels selon le bail ; quittances et relances envoyées à la demande seulement.
7. Aucun calcul de révision ou régularisation n'est appliqué avant validation ; son détail est explicable au locataire.
8. Une candidature ne change jamais d'étape sans validation du propriétaire ; la visite peut avancer en parallèle mais bloque la création du bail si elle n'est pas effectuée.
9. La transformation en locataire actuel exige les cinq conditions d'entrée et la validation du propriétaire.
10. Baux PDF, signature, états des lieux et interventions sont rattachés aux bonnes personnes et au bon bien.
11. Les interfaces des deux plateformes répondent au périmètre d'intégration confirmé après étude, ou une adaptation explicitement approuvée est documentée.
12. La navigation est validée sur maquettes et prototype HTML avant implémentation ; les fonctions et données existantes sont préservées.

## 14. Checklist hiérarchique proposée

- [ ] 1. Valider le cadrage
  - [ ] 1.1 Relire les exigences V1/V2 de ce document
  - [ ] 1.2 Valider le workflow précisé du kanban, les variantes de pièces et les automatismes
  - [ ] 1.3 Étudier les possibilités des plateformes et de signature
  - [ ] 1.4 Préciser les règles métier de calcul et les cas de bail commun
- [ ] 2. Concevoir l'expérience utilisateur
  - [ ] 2.1 Proposer l'organisation globale et les parcours
  - [ ] 2.2 Réaliser et valider les maquettes
  - [ ] 2.3 Produire et valider le prototype HTML navigable
- [ ] 3. Préparer l'implémentation
  - [ ] 3.1 Définir les modèles, intégrations, migrations et protections d'accès
  - [ ] 3.2 Définir les lots, tests et critères détaillés ; maintenir le suivi `codex-progress.html` déjà créé à la demande du propriétaire
  - [ ] 3.3 Préparer la préservation des données sur la branche `gestion` déjà créée
- [ ] 4. Implémenter le périmètre approuvé
  - [ ] 4.1 Comptes, accès et navigation
  - [ ] 4.2 Biens, documents, personnes et contrats ; préserver le module fiscal existant
  - [ ] 4.3 Soldes, paiements, documents locatifs et e-mails
  - [ ] 4.4 Révision et régularisation
  - [ ] 4.5 Annonces, candidatures, baux et signature
  - [ ] 4.6 Entrées, sorties, prestataires et interventions
- [ ] 5. Vérifier la livraison
  - [ ] 5.1 Tests métier, accès entre propriétaires et non-régression fiscale
  - [ ] 5.2 Parcours de bout en bout et cas d'échec des intégrations
  - [ ] 5.3 Recette sur les critères validés

L'ordre technique pourra être ajusté sans changer le résultat approuvé. Aucune ligne n'est déclarée terminée avant sa vérification. La réalisation peut être découpée en lots tout en conservant l'ensemble de la V1 convenue.

## 15. Décisions encore nécessaires

Avant les maquettes : valider ce périmètre, préciser les colonnes/actions du kanban et les contraintes d'intégration susceptibles d'affecter les parcours.

Avant les modules concernés : modèles de dossier/bail/état des lieux, règles des calculs, répartition par personne dans un bail commun, traitement des impayés/provisions dans les régularisations, détails de la sortie.

Avant mise en service : cadre d’utilisation de la V1 avec adresse non vérifiée, hébergement, inscription des propriétaires, envoi des e-mails, choix de signature et comptes plateforme, stockage et conservation des documents. Les données existantes devront être rattachées au compte de leur propriétaire lors de l'introduction des accès privés.

Les décisions ouvertes ne doivent pas être remplacées silencieusement par une hypothèse qui change le périmètre.

## 16. Corrections intégrées le 27 octobre 2026

- Suivi obligatoire par liste de tâches HTML conformément à l’AGENTS.md, sans attendre l’implémentation pour le rendre visible.
- Branche de travail : `gestion`.
- V1 avec simple adresse e-mail ; code de confirmation reporté à la V2.
- Enable Banking réutilisé tel qu’existant ; fiscalité protégée contre les changements fonctionnels.
- Décision d’ergonomie encore ouverte : Transactions dans son emplacement actuel ou module à part entière.
- Parcours candidat détaillé à partir des étapes et champs fournis, y compris création manuelle, validations propriétaire, PDF avec pièces et sous-tâches d’emménagement.


### Précision validée par la demande du 27 octobre — périmètre par bien

La fiche du bien doit afficher et permettre de choisir « LMNP · régime réel », « Autre régime » ou « SCI ». Seuls les biens LMNP au réel contribuent aux calculs comptables et fiscaux LMNP existants. Les autres biens conservent la gestion et les transactions, sans calcul SCI ou autre régime dans la V1. Ce changement de périmètre ne doit pas réécrire les règles de calcul existantes : avec tous les biens au réel, les résultats doivent rester identiques. Le traitement historique d’un changement de régime doit être défini avant implémentation. Maquette v5 uniquement : aucun filtre appliqué aux données réelles.
