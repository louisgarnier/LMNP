// Extension V6 — Loyers & charges. Maquette locale uniquement : aucune API,
// aucun e-mail, aucune écriture comptable ni calcul juridique certifié.
var rentDemo = window.rentDemo || {
  year: 2026,
  openingBalance: '0 €',
  allocationConfirmed: false,
  regularisationValidated: false,
  revisionValidated: false
};

function rentEur(value) {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
}

function rentClose() {
  document.getElementById('detail').close();
}

function rentTrackCell(name, month, cell) {
  var due = cell.due;
  var received = cell.received;
  if (!due) return '—';
  var late = received < due;
  var text = rentEur(received).replace(',00', '') + ' / ' + rentEur(due).replace(',00', '');
  return '<button class="' + (late ? 'late' : '') + '" onclick="payment(\'' + name + '\',\'' + month + '\')" aria-label="Détail ' + name + ', ' + month + '">' + text + '</button>' + (cell.note ? '<small class="rent-detail">' + cell.note + '</small>' : '');
}

function rentDataForYear(year) {
  var months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'];
  function cells(first, last, shortMonth, noteMonth) {
    return months.map(function(month, index) {
      var due = index >= first && index <= last ? 450 : 0;
      return { due: due, received: due && index === shortMonth ? 300 : due, note: index === noteMonth ? 'virement 900 € réparti' : '' };
    });
  }
  if (year === 2025) {
    return {
      label: 'Historique fictif de démonstration',
      tenants: [
        { name: 'Léa Martin', cells: cells(0, 11) },
        { name: 'Alex Bernard', cells: cells(3, 11) },
        { name: 'Nora Petit', cells: cells(6, 11) },
        { name: 'Sam Robert', cells: cells(9, 11) }
      ]
    };
  }
  var nora = cells(0, 10);
  nora[8].note = 'virement 900 € réparti sur sept. + oct.';
  return {
    label: 'Suivi fictif de démonstration',
    tenants: [
      { name: 'Léa Martin', cells: cells(0, 10) },
      { name: 'Alex Bernard', cells: cells(0, 10, 9) },
      { name: 'Nora Petit', cells: nora },
      { name: 'Sam Robert', cells: cells(3, 10) }
    ]
  };
}

function rentTotals(data) {
  return data.tenants.reduce(function(total, tenant) {
    tenant.cells.forEach(function(cell) { total.due += cell.due; total.received += cell.received; });
    return total;
  }, { due: 0, received: 0 });
}

function rents() {
  if (model.property !== 'evry') {
    var emptyContent = '<section class="panel"><h2>Aucune location suivie pour ce bien</h2><p class="muted">Ce bien ne reprend pas les locataires de démonstration d’Évry. Vous pourrez commencer par saisir un solde de départ, créer le premier bail ou relier les transactions existantes.</p><div class="card-actions">'
      + btn('Saisir un solde de départ', 'openingBalance()', true)
      + btn('Créer le premier bail', 'lease()')
      + btn('Voir le scénario détaillé d’Évry', "model.property='evry';render()")
      + '</div></section><div class="note">État vide de maquette : aucune donnée locative, transaction ou écriture comptable n’est créée.</div>';
    return title('Loyers & charges', P().name + ' · démarrer le suivi locatif de ce bien', btn('Voir les transactions →', "go('transactions')"))
      + tabs(['Suivi des loyers', 'Appels & quittances', 'Révision du loyer', 'Régularisation'], 'rentTab') + emptyContent;
  }
  var months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'];
  var data = rentDataForYear(rentDemo.year);
  var totals = rentTotals(data);
  var rows = data.tenants.map(function(tenant) {
    var remainder = tenant.cells.reduce(function(value, cell) { return value + cell.due - cell.received; }, 0);
    return [tenant.name, tenant.cells.map(function(cell, i) { return rentTrackCell(tenant.name, months[i], cell); }), remainder];
  });
  var content;
  if (model.rentTab === 'Suivi des loyers') {
    content = '<div class="metrics rent-metrics">'
      + '<div class="metric"><small>Attendu · ' + rentDemo.year + '</small><strong>' + rentEur(totals.due) + '</strong><small>' + (totals.due / 450) + ' échéances de 450 €</small></div>'
      + '<div class="metric"><small>Reçu et affecté</small><strong>' + rentEur(totals.received) + '</strong><small>' + (rentDemo.year === 2026 ? 'Le virement de Nora couvre deux mois' : 'Historique de démonstration') + '</small></div>'
      + '<div class="metric"><small>À recevoir</small><strong>' + rentEur(totals.due - totals.received) + '</strong><small>' + (totals.due === totals.received ? 'Aucun impayé illustré' : 'Alex · octobre') + '</small></div>'
      + '<div class="metric"><small>Dépôts de garantie</small><strong>1 640 €</strong><small>Suivis séparément des loyers</small></div></div>'
      + '<div class="toolbar"><label>Année <select aria-label="Année du suivi des loyers" onchange="rentDemo.year=Number(this.value);render()"><option value="2026" ' + (rentDemo.year === 2026 ? 'selected' : '') + '>2026</option><option value="2025" ' + (rentDemo.year === 2025 ? 'selected' : '') + '>2025</option></select></label><span class="muted">' + data.label + ' · montant reçu / montant dû · cliquez sur une case pour voir les mouvements</span><span class="spacer"></span>'
      + btn('Saisir un solde de départ', 'openingBalance()') + '</div>'
      + table(['Locataire',].concat(months).concat(['À recevoir']), rows.map(function(row) { return [row[0]].concat(row[1]).concat([row[2] ? '<strong>' + rentEur(row[2]) + '</strong>' : '0 €']); }), 'rent')
      + '<section class="panel rent-deposits"><h2>Dépôts de garantie</h2>'
      + table(['Locataire', 'Montant reçu', 'Statut', 'Lien au bail'], [['Léa Martin', '410 €', badge('Reçu', 'green'), btn('Voir le dépôt', "rentDeposit('Léa Martin')")], ['Alex Bernard', '410 €', badge('Reçu', 'green'), btn('Voir le dépôt', "rentDeposit('Alex Bernard')")], ['Nora Petit', '410 €', badge('Reçu', 'green'), btn('Voir le dépôt', "rentDeposit('Nora Petit')")], ['Sam Robert', '410 €', badge('Reçu', 'green'), btn('Voir le dépôt', "rentDeposit('Sam Robert')")]])
      + '</section><div class="note">Une transaction bancaire reste unique. Le propriétaire peut répartir son montant entre plusieurs mois, et plusieurs mouvements peuvent contribuer au même mois. Les dépôts de garantie sont suivis à part et ne couvrent jamais automatiquement un loyer.</div>';
  } else if (model.rentTab === 'Appels & quittances') {
    content = rentCalls();
  } else if (model.rentTab === 'Révision du loyer') {
    content = rentRevision();
  } else {
    content = rentRegularisation();
  }
  return title('Loyers & charges', P().name + ' · suivi locatif distinct des transactions comptables', btn('Voir les transactions →', "go('transactions')"))
    + tabs(['Suivi des loyers', 'Appels & quittances', 'Révision du loyer', 'Régularisation'], 'rentTab') + content;
}

function payment(name, month) {
  var monthIndex = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'].indexOf(month);
  var tenant = rentDataForYear(rentDemo.year).tenants.filter(function(item) { return item.name === name; })[0];
  var cell = tenant.cells[monthIndex];
  var partial = cell.due && cell.received < cell.due;
  var advance = rentDemo.year === 2026 && name === 'Nora Petit' && (month === 'Sep' || month === 'Oct');
  var lines = partial
    ? [['03 oct. · Virement Alex', '300 €', 'Octobre ' + rentDemo.year, '300 €'], ['25 oct. · Relance manuelle', '—', 'Reste à recevoir', '150 €']]
    : advance
      ? [['02 sept. · Virement Nora', '900 €', 'Septembre ' + rentDemo.year, '450 €'], ['02 sept. · Même mouvement', '—', 'Octobre ' + rentDemo.year, '450 €']]
      : [['05 ' + month.toLowerCase() + ' · Virement ' + name.split(' ')[0], rentEur(cell.received), month + ' ' + rentDemo.year, rentEur(cell.received)]];
  var received = cell.received;
  modal('Paiements · ' + name, '<p>' + month + ' ' + rentDemo.year + ' · ' + P().name + '</p>'
    + table(['Mouvement ou action', 'Montant', 'Période affectée', 'Part affectée'], lines)
    + table(['Dû', 'Affecté', 'Reste'], [[rentEur(cell.due), rentEur(received), rentEur(cell.due - received)]])
    + '<p class="muted">Les valeurs sont fictives et représentent une simple affectation de suivi ; les transactions comptables existantes ne sont pas changées.</p>'
    + '<div class="card-actions">' + btn('Affecter un autre paiement', "rentAllocation('" + name + "','" + month + "')", true) + btn('Préparer une relance', "rentReminder('" + name + "','" + month + "')") + btn('Voir les transactions', "rentClose();go('transactions')") + '</div>');
}

// Point d’entrée depuis la liste des transactions : même parcours d’affectation
// que depuis le suivi des loyers, sans modifier le mouvement bancaire source.
function assign() {
  rentAllocation('Locataire à préciser', 'Octobre');
}

function rentAllocation(name, month) {
  modal('Affecter un paiement · ' + name, '<p>Simulation d’affectation à ' + month + ' ' + rentDemo.year + '. Le plafond est le montant disponible du mouvement sélectionné.</p><div class="form">'
    + '<label>Mouvement bancaire <select id="rent-movement"><option value="300">Virement du 14 novembre · 300 € non affectés</option><option value="600">Virement du 20 novembre · 600 € non affectés</option></select></label>'
    + '<label>Mois à couvrir <select id="rent-period"><option>' + month + ' ' + rentDemo.year + '</option><option>Novembre ' + rentDemo.year + '</option><option>Décembre ' + rentDemo.year + '</option></select></label>'
    + '<label>Montant à affecter <input id="rent-amount" inputmode="decimal" value="150" aria-label="Montant à affecter"></label>'
    + '<p class="muted">Un même mouvement peut être réparti entre plusieurs périodes tant que son solde disponible n’est pas dépassé.</p>'
    + btn('Valider l’affectation simulée', 'rentConfirmAllocation()', true) + '</div>');
}

function rentConfirmAllocation() {
  var amount = Number(String(document.getElementById('rent-amount').value).replace(',', '.'));
  var available = Number(document.getElementById('rent-movement').value);
  if (!Number.isFinite(amount) || amount <= 0) { notice('Saisissez un montant positif.'); return; }
  if (amount > available) { notice('Le montant dépasse les ' + rentEur(available) + ' disponibles sur ce mouvement.'); return; }
  rentDemo.allocationConfirmed = true;
  rentClose();
  go('rents');
  notice('Affectation simulée validée : aucun mouvement bancaire réel n’a été modifié.');
}

function openingBalance() {
  modal('Solde de départ', '<p>À utiliser lors de la reprise d’un bien, sans ressaisir tout l’historique.</p><div class="form">'
    + '<label>Locataire <select><option>Alex Bernard</option><option>Léa Martin</option><option>Nora Petit</option></select></label>'
    + '<label>Date de reprise <input type="date" value="2026-01-01"></label>'
    + '<label>Situation <select id="rent-opening-kind"><option value="Dette du locataire">Dette du locataire</option><option value="Trop-perçu">Trop-perçu</option><option value="À jour">À jour</option></select></label>'
    + '<label>Montant <input id="rent-opening-amount" inputmode="decimal" value="150" aria-label="Montant du solde de départ"></label>'
    + btn('Enregistrer dans la maquette', 'rentSaveOpeningBalance()', true) + '</div>');
}

function rentSaveOpeningBalance() {
  var amount = Number(String(document.getElementById('rent-opening-amount').value).replace(',', '.'));
  if (!Number.isFinite(amount) || amount < 0) { notice('Saisissez un montant égal ou supérieur à zéro.'); return; }
  rentDemo.openingBalance = rentEur(amount);
  rentClose();
  notice('Solde de départ simulé : ' + rentDemo.openingBalance + '. Aucune donnée réelle sauvegardée.');
}

function rentDeposit(name) {
  modal('Dépôt de garantie · ' + name, '<p><strong>410 € reçus</strong> · dépôt distinct du suivi mensuel des loyers.</p><dl><dt>Bail</dt><dd>Contrat individuel · chambre</dd><dt>Encaissement</dt><dd>Transaction existante à rattacher lors de l’implémentation</dd><dt>Restitution</dt><dd>À suivre à la sortie, après l’état des lieux et la régularisation</dd></dl><div class="card-actions">' + btn('Voir le bail', 'lease()') + btn('Préparer la sortie', 'tenant()') + '</div>');
}

function rentCalls() {
  return '<section class="panel"><h2>Appels de loyer par bail</h2><p class="muted">Date et mode d’envoi réglables par contrat. L’envoi est une simulation : aucun e-mail n’est envoyé depuis cette maquette.</p>'
    + table(['Bail', 'Date prévue', 'Mode', 'Document', 'Action'], [
      ['Léa · chambre 1', 'Le 25 de chaque mois', badge('Automatique', 'green'), 'Appel octobre · 450 €', btn('Aperçu', "rentCallPreview('Léa Martin','Appel de loyer')")],
      ['Alex · chambre 2', 'Le 28 de chaque mois', badge('Manuel', 'grey'), 'Appel octobre · 450 €', btn('Aperçu', "rentCallPreview('Alex Bernard','Appel de loyer')")],
      ['Nora · chambre 3', 'Le 25 de chaque mois', badge('Automatique', 'green'), 'Appel octobre · 450 €', btn('Aperçu', "rentCallPreview('Nora Petit','Appel de loyer')")]
    ]) + '<div class="card-actions">' + btn('Régler un appel par bail', 'rentCallSettings()', true) + btn('Journal des envois', 'rentSendLog()') + '</div></section>'
    + '<section class="panel" style="margin-top:20px"><h2>Quittances, relances et solde</h2>'
    + table(['Locataire', 'Période', 'Situation', 'Action'], [
      ['Léa Martin', 'Septembre ' + rentDemo.year, badge('Réglé', 'green'), btn('Préparer la quittance', "rentCallPreview('Léa Martin','Quittance')")],
      ['Alex Bernard', 'Octobre ' + rentDemo.year, badge('150 € restant', 'orange'), btn('Préparer une relance', "rentReminder('Alex Bernard','Octobre')")],
      ['Nora Petit', 'Septembre ' + rentDemo.year, badge('Réglé', 'green'), btn('Préparer la quittance', "rentCallPreview('Nora Petit','Quittance')")]
    ]) + '<p class="reviewbar">Quittances et relances sont déclenchées manuellement par le propriétaire en V1. Les relances automatiques relèvent de la V2.</p></section>';
}

function rentCallSettings() {
  modal('Réglage de l’appel · bail de Léa Martin', '<div class="form"><label>Jour d’envoi <input type="number" min="1" max="28" value="25" aria-label="Jour d’envoi"></label><label>Mode <select><option>Automatique</option><option>Manuel</option></select></label><label>Destinataire <input value="lea@exemple.fr" type="email"></label><p class="muted">Le propriétaire pourra valider ou ajuster cet envoi avant sa mise en œuvre. Cette maquette n’enregistre pas le réglage.</p>' + btn('Prévisualiser le réglage', "rentClose();notice('Réglage d’appel simulé : aucune préférence réelle modifiée.')", true) + '</div>');
}

function rentCallPreview(name, type) {
  var receipt = type === 'Quittance';
  modal(type + ' · aperçu', '<section class="rent-document"><h2>' + type + '</h2><p><strong>' + P().name + '</strong><br>' + name + '<br>Période : octobre ' + rentDemo.year + '</p><hr><dl><dt>Loyer hors charges</dt><dd>410 €</dd><dt>Charges</dt><dd>40 €</dd><dt>Total</dt><dd><strong>450 €</strong></dd>' + (receipt ? '<dt>Statut</dt><dd>Intégralement réglé</dd>' : '<dt>Date d’exigibilité</dt><dd>5 octobre ' + rentDemo.year + '</dd>') + '</dl><p class="muted">Aperçu fictif : le format final du document et l’e-mail seront validés avant développement.</p></section><div class="card-actions">' + btn('Simuler l’envoi manuel', "rentClose();notice('Envoi simulé : aucun e-mail n’a été transmis.')", true) + btn('Fermer', 'rentClose()') + '</div>');
}

function rentReminder(name, period) {
  modal('Relance de paiement · aperçu e-mail', '<p>À : ' + name + ' · période : ' + period + ' ' + rentDemo.year + '</p><div class="note"><strong>Objet : rappel de règlement</strong><br>Bonjour, sauf erreur de notre part, il reste 150 € à régler au titre du loyer d’octobre. Merci de nous indiquer la date de votre règlement.</div><p class="muted">Le propriétaire déclenche l’envoi manuellement. Le contenu reste modifiable avant l’envoi réel.</p><div class="card-actions">' + btn('Simuler l’envoi', "rentClose();notice('Relance simulée : aucun e-mail transmis.')", true) + btn('Fermer', 'rentClose()') + '</div>');
}

function rentSendLog() {
  modal('Journal des envois · simulation', table(['Date', 'Document', 'Destinataire', 'État', 'Action'], [
    ['25 oct. ' + rentDemo.year, 'Appel de loyer', 'Léa Martin', badge('Envoyé', 'green'), '—'],
    ['25 oct. ' + rentDemo.year, 'Appel de loyer', 'Nora Petit', badge('Échec', 'orange'), btn('Réessayer', "rentClose();notice('Nouvel essai simulé : aucun e-mail transmis.')")],
    ['26 oct. ' + rentDemo.year, 'Quittance', 'Léa Martin', badge('Envoyé', 'green'), '—']
  ]) + '<p class="muted">Le suivi d’état, la date et la possibilité de réessayer sont illustrés sans connexion à une messagerie.</p>');
}

function rentRevision() {
  return '<section class="panel"><h2>Révision du loyer · bail de Léa Martin</h2><p class="muted">Illustration du parcours demandé. Les indices et le résultat ci-dessous sont fictifs et ne constituent pas un calcul légal certifié.</p>'
    + '<div class="fieldgrid"><label>Date prévue de révision <input type="date" value="2026-09-16" readonly></label><label>Indice inscrit au bail <select disabled><option>IRL · trimestre 2</option><option>IRL · trimestre 3</option></select></label><label>Indice de départ <input value="145,17" readonly></label><label>Indice publié retenu <input value="146,90" readonly></label></div><p class="muted">Exemple figé dans la maquette : la saisie et le moteur de calcul seront conçus et vérifiés lors de l’implémentation.</p>'
    + '<div class="comparison" style="margin-top:20px"><section class="panel"><h3>Montant actuel</h3><strong style="font-size:26px">410 €</strong><p>Hors charges</p></section><section class="panel"><h3>Simulation indicative</h3><strong style="font-size:26px">414,89 €</strong><p>Variation présentée à vérifier avant validation.</p></section></div>'
    + '<div class="note">Détail illustratif : 410 € × 146,90 ÷ 145,17. La date d’effet, l’indice applicable et les conditions du bail devront être contrôlés par le propriétaire avant toute application.</div>'
    + '<div class="card-actions">' + btn('Valider la révision dans la maquette', 'rentValidateRevision()', true) + btn('Aperçu de l’e-mail explicatif', 'rentRevisionMail()') + '</div></section>';
}

function rentValidateRevision() {
  rentDemo.revisionValidated = true;
  notice('Révision simulée validée par le propriétaire. Aucun bail ni loyer réel n’a été modifié.');
  render();
}

function rentRevisionMail() {
  modal('Révision du loyer · aperçu e-mail', '<p>À : Léa Martin</p><div class="note"><strong>Objet : information sur la révision de votre loyer</strong><br>Votre loyer hors charges évoluerait de 410 € à 414,89 € à compter de la date d’effet à confirmer. L’aperçu inclut l’indice et le détail de calcul choisi par le propriétaire.</div><p class="muted">Aucun envoi réel. La validation propriétaire et le contrôle du bail restent nécessaires.</p><div class="card-actions">' + btn('Simuler l’envoi', "rentClose();notice('E-mail simulé : aucun message transmis.')", true) + btn('Fermer', 'rentClose()') + '</div>');
}

function rentRegularisation() {
  var status = rentDemo.regularisationValidated ? badge('Validée dans la maquette', 'green') : badge('Validation propriétaire requise', 'orange');
  return '<section class="panel"><div class="head"><div><h2>Régularisation des charges · ' + rentDemo.year + '</h2><p class="muted">Scénario fictif distinct du tableau des loyers · période du 01/01/' + rentDemo.year + ' au 31/12/' + rentDemo.year + ' · règle produit demandée : prorata 30/360.</p></div>' + status + '</div>'
    + table(['Charge payée par le propriétaire', 'Montant', 'Justificatif'], [['Eau et électricité', '960 €', 'Factures à rattacher'], ['Charges de copropriété récupérables', '1 440 €', 'Décompte annuel'], ['<strong>Total</strong>', '<strong>2 400 €</strong>', '—']])
    + '<h3 style="margin-top:24px">Occupation et répartition illustrée</h3>'
    + table(['Période', 'Occupants', 'Base 30/360', 'Part de charges'], [['01/01 — 31/03', 'Aucun occupant', '90 / 360', '600 € · propriétaire'], ['01/04 — 31/12', 'Léa, Alex, Nora, Sam · 1 chambre vacante', '270 / 360', '1 800 € · 450 € par locataire']])
    + '<p class="muted">Quand un logement ou une chambre est vacante mais que d’autres locataires sont présents, la part de la chambre vacante est répartie entre eux selon la règle définie. S’il n’y a aucun occupant, la charge reste au propriétaire.</p>'
    + '<h3 style="margin-top:24px">Comparaison avec les provisions</h3>'
    + table(['Locataire', 'Charges réparties', 'Provisions versées', 'Solde'], [['Léa Martin', '450 €', '360 €', '<strong>90 € à demander</strong>'], ['Alex Bernard', '450 €', '360 €', '<strong>90 € à demander</strong>'], ['Nora Petit', '450 €', '360 €', '<strong>90 € à demander</strong>'], ['Sam Robert', '450 €', '360 €', '<strong>90 € à demander</strong>'], ['<strong>Total locataires</strong>', '<strong>1 800 €</strong>', '<strong>1 440 €</strong>', '<strong>360 €</strong>']])
    + '<div class="note">Ces totaux sont figés pour l’exemple et ne se recalculent pas dans la maquette. Le scénario ne réutilise ni les locataires, ni les périodes, ni les paiements affichés dans le suivi des loyers. Il illustre seulement la règle 30/360 demandée, sans exécuter de calcul comptable ou juridique réel.</div>'
    + '<div class="card-actions">' + btn('Valider la régularisation dans la maquette', 'rentValidateRegularisation()', true) + btn('Aperçu de l’e-mail explicatif', 'rentRegularisationMail()') + '</div></section>';
}

function rentValidateRegularisation() {
  rentDemo.regularisationValidated = true;
  notice('Régularisation simulée validée par le propriétaire. Aucun montant réel n’a été enregistré.');
  render();
}

function rentRegularisationMail() {
  modal('Régularisation des charges · aperçu e-mail', '<p>À : Alex Bernard · exercice ' + rentDemo.year + '</p><div class="note"><strong>Objet : régularisation annuelle des charges</strong><br>Charges réparties : 450 € · provisions versées : 360 € · solde à régulariser : 90 €. Le message joint le détail de période et de répartition validé par le propriétaire.</div><p class="muted">Aucun envoi réel. Le propriétaire relit et déclenche l’e-mail manuellement.</p><div class="card-actions">' + btn('Simuler l’envoi', "rentClose();notice('E-mail simulé : aucun message transmis.')", true) + btn('Fermer', 'rentClose()') + '</div>');
}
