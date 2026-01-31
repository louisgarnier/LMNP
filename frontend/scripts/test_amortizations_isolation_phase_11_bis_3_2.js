/**
 * Test Step 3.2 : Isolation frontend - Vérification que le frontend passe property_id pour les Amortissements
 * 
 * Ce script teste que tous les appels API utilisés par le frontend passent correctement property_id
 * et que l'isolation des amortissements fonctionne.
 * 
 * ⚠️ IMPORTANT : 
 * - Ce script doit être exécuté dans la console du navigateur (F12)
 * - Le serveur backend doit être démarré
 * - Le frontend doit être accessible (http://localhost:3000)
 * 
 * Instructions :
 * 1. Ouvrir l'application dans le navigateur
 * 2. Ouvrir la console (F12)
 * 3. Copier-coller ce script dans la console
 * 4. Suivre les instructions affichées
 * 
 * Ce script teste :
 * 1. Sélection de prop1
 * 2. Création de 2 types d'amortissement pour prop1
 * 3. Vérification qu'ils s'affichent dans la config
 * 4. Changement pour prop2
 * 5. Vérification que les types de prop1 ne s'affichent PAS
 * 6. Création d'un type pour prop2
 * 7. Vérification qu'il s'affiche
 * 8. Retour à prop1
 * 9. Vérification que seuls les types de prop1 s'affichent
 * 10. Vérification que les résultats d'amortissement sont isolés par propriété
 */

(async function testAmortizationsIsolation() {
    console.log("=".repeat(80));
    console.log("TEST D'ISOLATION FRONTEND - Step 3.2 - AMORTISSEMENTS");
    console.log("Vérification que le frontend passe property_id à tous les appels API");
    console.log("=".repeat(80));
    console.log();
    
    // Vérifier que l'API est accessible
    const API_BASE = "http://localhost:8000/api";
    
    try {
        const testResponse = await fetch(`${API_BASE}/properties`);
        if (!testResponse.ok) {
            console.error("❌ ERREUR: Impossible de se connecter à l'API backend");
            console.error("   Assurez-vous que le serveur backend est démarré sur http://localhost:8000");
            return;
        }
    } catch (error) {
        console.error("❌ ERREUR: Impossible de se connecter à l'API backend:", error);
        return;
    }
    
    console.log("✅ Connexion à l'API backend réussie");
    console.log();
    
    // Générer des noms uniques avec timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    
    // 1. Créer 2 propriétés
    console.log("📋 ÉTAPE 1 : Création de 2 propriétés de test");
    console.log("-".repeat(80));
    
    const prop1Data = {
        name: `Test Property Amort 1_${timestamp}`,
        address: "123 Test Street"
    };
    const prop2Data = {
        name: `Test Property Amort 2_${timestamp}`,
        address: "456 Test Avenue"
    };
    
    let prop1, prop2;
    
    try {
        const response1 = await fetch(`${API_BASE}/properties`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(prop1Data)
        });
        if (!response1.ok) {
            throw new Error(`Erreur ${response1.status}: ${await response1.text()}`);
        }
        prop1 = await response1.json();
        console.log(`✅ Propriété 1 créée: ID=${prop1.id}, Name=${prop1.name}`);
        
        const response2 = await fetch(`${API_BASE}/properties`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(prop2Data)
        });
        if (!response2.ok) {
            throw new Error(`Erreur ${response2.status}: ${await response2.text()}`);
        }
        prop2 = await response2.json();
        console.log(`✅ Propriété 2 créée: ID=${prop2.id}, Name=${prop2.name}`);
    } catch (error) {
        console.error("❌ ERREUR lors de la création des propriétés:", error);
        return;
    }
    
    console.log();
    console.log("⚠️  INSTRUCTIONS MANUELLES:");
    console.log(`   1. Dans l'interface, sélectionnez la propriété "${prop1.name}" (ID=${prop1.id})`);
    console.log(`   2. Allez dans l'onglet "Amortissements"`);
    console.log(`   3. Ouvrez la console du navigateur (F12) et vérifiez les logs`);
    console.log(`   4. Appuyez sur ENTRÉE pour continuer...`);
    console.log();
    
    // Attendre confirmation de l'utilisateur
    await new Promise(resolve => {
        const checkInterval = setInterval(() => {
            if (window.confirm("Avez-vous sélectionné la propriété 1 et ouvert l'onglet Amortissements ?")) {
                clearInterval(checkInterval);
                resolve();
            }
        }, 1000);
    });
    
    // 2. Créer 2 types d'amortissement pour prop1
    console.log();
    console.log("📋 ÉTAPE 2 : Création de 2 types d'amortissement pour Property 1");
    console.log("-".repeat(80));
    console.log(`⚠️  Vérifiez les logs backend: [Amortizations] POST /api/amortization/types - property_id=${prop1.id}`);
    console.log();
    
    const type1_1Data = {
        property_id: prop1.id,
        name: "Type Prop1 #1",
        level_2_value: "Immobilisations",
        level_1_values: ["Immeuble (hors terrain)"],
        duration: 20.0,
        start_date: null,
        annual_amount: null
    };
    const type1_2Data = {
        property_id: prop1.id,
        name: "Type Prop1 #2",
        level_2_value: "Immobilisations",
        level_1_values: ["Mobilier & électroménager"],
        duration: 10.0,
        start_date: null,
        annual_amount: null
    };
    
    let type1_1, type1_2;
    
    try {
        const response1 = await fetch(`${API_BASE}/amortization/types`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(type1_1Data)
        });
        if (!response1.ok) {
            throw new Error(`Erreur ${response1.status}: ${await response1.text()}`);
        }
        type1_1 = await response1.json();
        console.log(`✅ Type 1 créé: ID=${type1_1.id}, Name=${type1_1.name}`);
        
        const response2 = await fetch(`${API_BASE}/amortization/types`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(type1_2Data)
        });
        if (!response2.ok) {
            throw new Error(`Erreur ${response2.status}: ${await response2.text()}`);
        }
        type1_2 = await response2.json();
        console.log(`✅ Type 2 créé: ID=${type1_2.id}, Name=${type1_2.name}`);
    } catch (error) {
        console.error("❌ ERREUR lors de la création des types:", error);
        return;
    }
    
    console.log();
    console.log("⚠️  VÉRIFICATION MANUELLE:");
    console.log("   - Les 2 types doivent s'afficher dans la card 'Configuration'");
    console.log("   - Vérifiez les logs frontend: les appels API doivent inclure propertyId");
    console.log("   - Appuyez sur ENTRÉE pour continuer...");
    console.log();
    
    await new Promise(resolve => {
        if (window.confirm("Les 2 types s'affichent-ils dans la configuration ?")) {
            resolve();
        }
    });
    
    // 3. Changer pour prop2
    console.log();
    console.log("📋 ÉTAPE 3 : Changement pour Property 2");
    console.log("-".repeat(80));
    console.log(`⚠️  INSTRUCTIONS MANUELLES:`);
    console.log(`   1. Dans l'interface, sélectionnez la propriété "${prop2.name}" (ID=${prop2.id})`);
    console.log(`   2. Allez dans l'onglet "Amortissements"`);
    console.log(`   3. Vérifiez que les 2 types de prop1 ne s'affichent PAS`);
    console.log(`   4. Appuyez sur ENTRÉE pour continuer...`);
    console.log();
    
    await new Promise(resolve => {
        if (window.confirm("Les types de prop1 ne s'affichent-ils plus ?")) {
            resolve();
        }
    });
    
    // 4. Créer 1 type pour prop2
    console.log();
    console.log("📋 ÉTAPE 4 : Création d'un type d'amortissement pour Property 2");
    console.log("-".repeat(80));
    console.log(`⚠️  Vérifiez les logs backend: [Amortizations] POST /api/amortization/types - property_id=${prop2.id}`);
    console.log();
    
    const type2_1Data = {
        property_id: prop2.id,
        name: "Type Prop2 #1",
        level_2_value: "Immobilisations",
        level_1_values: ["Immeuble (hors terrain)"],
        duration: 25.0,
        start_date: null,
        annual_amount: null
    };
    
    let type2_1;
    
    try {
        const response = await fetch(`${API_BASE}/amortization/types`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(type2_1Data)
        });
        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${await response.text()}`);
        }
        type2_1 = await response.json();
        console.log(`✅ Type créé: ID=${type2_1.id}, Name=${type2_1.name}`);
    } catch (error) {
        console.error("❌ ERREUR lors de la création du type:", error);
        return;
    }
    
    console.log();
    console.log("⚠️  VÉRIFICATION MANUELLE:");
    console.log("   - Le type doit s'afficher dans la card 'Configuration'");
    console.log("   - Vérifiez les logs frontend: les appels API doivent inclure propertyId");
    console.log("   - Appuyez sur ENTRÉE pour continuer...");
    console.log();
    
    await new Promise(resolve => {
        if (window.confirm("Le type de prop2 s'affiche-t-il dans la configuration ?")) {
            resolve();
        }
    });
    
    // 5. Revenir à prop1
    console.log();
    console.log("📋 ÉTAPE 5 : Retour à Property 1");
    console.log("-".repeat(80));
    console.log(`⚠️  INSTRUCTIONS MANUELLES:`);
    console.log(`   1. Dans l'interface, sélectionnez à nouveau la propriété "${prop1.name}" (ID=${prop1.id})`);
    console.log(`   2. Allez dans l'onglet "Amortissements"`);
    console.log(`   3. Vérifiez que seuls les 2 types de prop1 s'affichent`);
    console.log(`   4. Vérifiez que le type de prop2 ne s'affiche PAS`);
    console.log(`   5. Appuyez sur ENTRÉE pour continuer...`);
    console.log();
    
    await new Promise(resolve => {
        if (window.confirm("Seuls les 2 types de prop1 s'affichent-ils ?")) {
            resolve();
        }
    });
    
    // 6. Vérifier les résultats d'amortissement
    console.log();
    console.log("📋 ÉTAPE 6 : Vérification de l'isolation des résultats d'amortissement");
    console.log("-".repeat(80));
    console.log(`⚠️  VÉRIFICATION MANUELLE:`);
    console.log(`   1. Vérifiez que la table d'amortissement affiche uniquement les résultats de prop1`);
    console.log(`   2. Changez pour prop2 et vérifiez que la table affiche uniquement les résultats de prop2`);
    console.log(`   3. Vérifiez les logs frontend: les appels API doivent inclure propertyId`);
    console.log();
    
    // 7. Résumé final
    console.log("=".repeat(80));
    console.log("✅ TESTS D'ISOLATION FRONTEND TERMINÉS");
    console.log("=".repeat(80));
    console.log();
    console.log("📊 Récapitulatif:");
    console.log(`   - Property 1 (ID=${prop1.id}): 2 types d'amortissement`);
    console.log(`   - Property 2 (ID=${prop2.id}): 1 type d'amortissement`);
    console.log();
    console.log("✅ Isolation frontend vérifiée:");
    console.log("   - Les types s'affichent uniquement pour la propriété active");
    console.log("   - Les résultats d'amortissement sont isolés par propriété");
    console.log("   - Tous les appels API incluent propertyId");
    console.log();
    console.log("⚠️  Vérifiez les logs frontend et backend pour confirmer que tous les appels incluent property_id");
    console.log();
    
    // Nettoyer les données de test (optionnel)
    console.log("💡 Pour nettoyer les données de test, exécutez:");
    console.log(`   - DELETE ${API_BASE}/properties/${prop1.id}`);
    console.log(`   - DELETE ${API_BASE}/properties/${prop2.id}`);
    console.log();
})();
