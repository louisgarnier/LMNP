/**
 * Script de vérification des erreurs frontend
 * 
 * Vérifie :
 * - Erreurs de compilation TypeScript
 * - Erreurs de lint
 * - Exports manquants
 * - Erreurs de build Next.js
 * 
 * Usage: node scripts/check_frontend_errors.js
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

const FRONTEND_DIR = path.join(__dirname, '..', 'frontend');
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const BLUE = '\x1b[34m';
const RESET = '\x1b[0m';

let hasErrors = false;
let hasWarnings = false;

function log(message, color = RESET) {
  console.log(`${color}${message}${RESET}`);
}

function logSection(title) {
  console.log(`\n${BLUE}${'='.repeat(60)}${RESET}`);
  log(`${BLUE}${title}${RESET}`);
  console.log(`${BLUE}${'='.repeat(60)}${RESET}\n`);
}

function checkTypeScript() {
  logSection('1. Vérification TypeScript');
  
  try {
    log('Compilation TypeScript...', YELLOW);
    execSync('npx tsc --noEmit', {
      cwd: FRONTEND_DIR,
      stdio: 'pipe',
    });
    log('✅ Aucune erreur TypeScript', GREEN);
    return true;
  } catch (error) {
    hasErrors = true;
    log('❌ Erreurs TypeScript détectées:', RED);
    console.log(error.stdout?.toString() || error.stderr?.toString());
    return false;
  }
}

function checkLint() {
  logSection('2. Vérification ESLint');
  
  try {
    log('Exécution ESLint...', YELLOW);
    const result = execSync('npm run lint 2>&1', {
      cwd: FRONTEND_DIR,
      stdio: 'pipe',
      encoding: 'utf-8',
    });
    
    if (result.includes('error') || result.includes('Error')) {
      hasErrors = true;
      log('❌ Erreurs ESLint détectées:', RED);
      console.log(result);
      return false;
    } else if (result.includes('warning') || result.includes('Warning')) {
      hasWarnings = true;
      log('⚠️  Avertissements ESLint détectés:', YELLOW);
      console.log(result);
      return true;
    } else {
      log('✅ Aucune erreur ESLint', GREEN);
      return true;
    }
  } catch (error) {
    hasErrors = true;
    log('❌ Erreurs ESLint détectées:', RED);
    console.log(error.stdout?.toString() || error.stderr?.toString());
    return false;
  }
}

function checkExports() {
  logSection('3. Vérification des exports');
  
  try {
    log('Vérification des exports TypeScript/JavaScript...', YELLOW);
    const verifyExportsScript = path.join(__dirname, 'verify_exports.js');
    // Utiliser require.resolve pour gérer les chemins avec espaces
    const scriptPath = require.resolve(verifyExportsScript);
    execSync(`node "${scriptPath}"`, {
      stdio: 'inherit',
      shell: true,
    });
    log('✅ Aucun problème d\'export détecté', GREEN);
    return true;
  } catch (error) {
    hasErrors = true;
    log('❌ Problèmes d\'export détectés:', RED);
    return false;
  }
}

function checkBuild() {
  logSection('4. Vérification du build Next.js');
  
  try {
    log('Build Next.js (mode production)...', YELLOW);
    log('⚠️  Note: Cette étape peut prendre quelques minutes...', YELLOW);
    
    execSync('npm run build', {
      cwd: FRONTEND_DIR,
      stdio: 'pipe',
      timeout: 300000, // 5 minutes max
    });
    
    log('✅ Build réussi', GREEN);
    return true;
  } catch (error) {
    hasErrors = true;
    log('❌ Erreurs de build détectées:', RED);
    const output = error.stdout?.toString() || error.stderr?.toString();
    console.log(output);
    
    // Extraire les erreurs importantes
    if (output.includes('Module not found')) {
      log('\n⚠️  Modules manquants détectés. Vérifiez les imports.', YELLOW);
    }
    if (output.includes('Cannot find module')) {
      log('\n⚠️  Modules introuvables. Vérifiez les chemins d\'import.', YELLOW);
    }
    if (output.includes('Type error')) {
      log('\n⚠️  Erreurs de type détectées. Vérifiez les types TypeScript.', YELLOW);
    }
    
    return false;
  }
}

function checkApiClient() {
  logSection('5. Vérification du client API');
  
  const clientPath = path.join(FRONTEND_DIR, 'src', 'api', 'client.ts');
  
  if (!fs.existsSync(clientPath)) {
    hasErrors = true;
    log('❌ Fichier client.ts introuvable', RED);
    return false;
  }
  
  const content = fs.readFileSync(clientPath, 'utf-8');
  
  // Vérifier les exports principaux
  const requiredExports = [
    'transactionsAPI',
    'mappingsAPI',
    'fileUploadAPI',
    'loanConfigsAPI',
    'loanPaymentsAPI',
  ];
  
  const missingExports = requiredExports.filter(exp => !content.includes(`export const ${exp}`));
  
  if (missingExports.length > 0) {
    hasWarnings = true;
    log(`⚠️  Exports API manquants: ${missingExports.join(', ')}`, YELLOW);
    return false;
  }
  
  log('✅ Client API valide', GREEN);
  return true;
}

function checkComponents() {
  logSection('6. Vérification des composants récents');
  
  const recentComponents = [
    'LoanPaymentFileUpload.tsx',
    'LoanPaymentPreviewModal.tsx',
    'LoanPaymentTable.tsx',
    'LoanConfigCard.tsx',
  ];
  
  let allExist = true;
  for (const component of recentComponents) {
    const componentPath = path.join(FRONTEND_DIR, 'src', 'components', component);
    if (!fs.existsSync(componentPath)) {
      hasErrors = true;
      log(`❌ Composant manquant: ${component}`, RED);
      allExist = false;
    }
  }
  
  if (allExist) {
    log('✅ Tous les composants récents existent', GREEN);
  }
  
  return allExist;
}

function checkApiEndpoints() {
  logSection('7. Vérification des endpoints API');
  
  const API_BASE_URL = process.env.API_URL || 'http://localhost:8000';
  const apiErrors = [];
  
  // Endpoints à tester
  const endpoints = [
    { method: 'GET', path: '/health', name: 'Health check' },
    { method: 'GET', path: '/api/loan-configs', name: 'Liste des configurations de crédit' },
    { method: 'GET', path: '/api/loan-payments', name: 'Liste des mensualités' },
    { method: 'GET', path: '/api/transactions?skip=0&limit=10', name: 'Liste des transactions' },
    // Test POST avec données invalides pour vérifier les erreurs 422
    { 
      method: 'POST', 
      path: '/api/loan-payments/preview', 
      name: 'Preview mensualités (test erreur 422)',
      body: 'multipart-empty', // Body vide pour tester l'erreur 422 "body.file: Field required"
      headers: {}
    },
  ];
  
  log(`Test des endpoints API sur ${API_BASE_URL}...`, YELLOW);
  
  return new Promise((resolve) => {
    let completed = 0;
    const total = endpoints.length;
    
    if (total === 0) {
      resolve(true);
      return;
    }
    
    endpoints.forEach(({ method, path, name, body, headers }) => {
      const url = new URL(path, API_BASE_URL);
      const client = url.protocol === 'https:' ? https : http;
      
      // Construire le body multipart/form-data si nécessaire
      let requestBody = null;
      let requestHeaders = { ...headers };
      
      if (body === 'multipart-empty') {
        // Créer un multipart/form-data avec un champ autre que "file" pour tester l'erreur 422
        // FastAPI retourne 422 "body.file: Field required" si le multipart est valide mais sans champ "file"
        const boundary = '----WebKitFormBoundary' + Math.random().toString(36).substring(2, 15);
        // Envoyer un champ "other_field" au lieu de "file" pour déclencher l'erreur 422
        requestBody = `--${boundary}\r\nContent-Disposition: form-data; name="other_field"\r\n\r\ntest\r\n--${boundary}--\r\n`;
        requestHeaders['Content-Type'] = `multipart/form-data; boundary=${boundary}`;
        requestHeaders['Content-Length'] = Buffer.byteLength(requestBody);
      } else if (body) {
        requestBody = body;
      }
      
      const options = {
        hostname: url.hostname,
        port: url.port || (url.protocol === 'https:' ? 443 : 80),
        path: url.pathname + url.search,
        method: method,
        timeout: 5000,
        headers: requestHeaders,
      };
      
      const req = client.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          completed++;
          
          if (res.statusCode >= 200 && res.statusCode < 300) {
            log(`  ✅ ${method} ${path} - ${res.statusCode}`, GREEN);
          } else if (res.statusCode === 404) {
            // 404 est acceptable pour certains endpoints
            log(`  ⚠️  ${method} ${path} - ${res.statusCode} (Non trouvé)`, YELLOW);
          } else {
            hasErrors = true;
            // Formater l'erreur comme dans la console du navigateur
            let errorData = data;
            try {
              const parsed = JSON.parse(data);
              // Extraire le message d'erreur de validation FastAPI
              if (parsed.detail && Array.isArray(parsed.detail)) {
                // Erreurs de validation FastAPI (422)
                const validationErrors = parsed.detail.map((err) => {
                  const loc = err.loc ? err.loc.join('.') : 'field';
                  return `${loc}: ${err.msg || err.type || 'Erreur'}`;
                }).join(', ');
                errorData = `{ "detail": [${validationErrors}] }`;
              } else if (parsed.detail) {
                errorData = JSON.stringify({ detail: parsed.detail }, null, 2);
              } else {
                errorData = JSON.stringify(parsed, null, 2);
              }
              // Limiter la taille
              errorData = errorData.substring(0, 500);
            } catch (e) {
              errorData = data.substring(0, 500);
            }
            const errorMsg = `Console Error ❌ [API] Erreur ${res.statusCode} (${path}): ${errorData}`;
            apiErrors.push(errorMsg);
            log(`  ❌ ${method} ${path} - ${res.statusCode}`, RED);
            log(`     ${errorMsg}`, RED);
          }
          
          if (completed === total) {
            if (apiErrors.length > 0) {
              log('\n📋 Résumé des erreurs API détectées:', YELLOW);
              apiErrors.forEach((err, idx) => {
                log(`  ${idx + 1}. ${err}`, RED);
              });
            }
            resolve(apiErrors.length === 0);
          }
        });
      });
      
      req.on('error', (error) => {
        completed++;
        hasErrors = true;
        const errorMsg = `Console Error ❌ [API] Erreur réseau (${path}): ${error.message}`;
        apiErrors.push(errorMsg);
        log(`  ❌ ${method} ${path} - Erreur réseau`, RED);
        log(`     ${errorMsg}`, RED);
        
        if (completed === total) {
          if (apiErrors.length > 0) {
            log('\n📋 Résumé des erreurs API détectées:', YELLOW);
            apiErrors.forEach((err, idx) => {
              log(`  ${idx + 1}. ${err}`, RED);
            });
          }
          resolve(apiErrors.length === 0);
        }
      });
      
      req.on('timeout', () => {
        req.destroy();
        completed++;
        hasErrors = true;
        const errorMsg = `Console Error ❌ [API] Timeout (${path}): Le serveur ne répond pas`;
        apiErrors.push(errorMsg);
        log(`  ❌ ${method} ${path} - Timeout`, RED);
        log(`     ${errorMsg}`, RED);
        
        if (completed === total) {
          if (apiErrors.length > 0) {
            log('\n📋 Résumé des erreurs API détectées:', YELLOW);
            apiErrors.forEach((err, idx) => {
              log(`  ${idx + 1}. ${err}`, RED);
            });
          }
          resolve(apiErrors.length === 0);
        }
      });
      
      // Envoyer le body si présent
      if (requestBody) {
        req.write(requestBody);
      }
      
      req.end();
    });
  });
}

async function main() {
  log(`\n${BLUE}🔍 Vérification complète du frontend${RESET}\n`);
  
  const results = {
    typescript: checkTypeScript(),
    lint: checkLint(),
    exports: checkExports(),
    apiClient: checkApiClient(),
    components: checkComponents(),
    // build: checkBuild(), // Commenté car long, décommenter si nécessaire
  };
  
  // Vérification des endpoints API (asynchrone)
  const apiCheck = await checkApiEndpoints();
  results.apiEndpoints = apiCheck;
  
  // Résumé
  logSection('Résumé');
  
  const allPassed = Object.values(results).every(r => r === true);
  
  if (allPassed && !hasErrors && !hasWarnings) {
    log('✅ Toutes les vérifications sont passées avec succès!', GREEN);
    process.exit(0);
  } else if (hasErrors) {
    log('❌ Des erreurs ont été détectées. Veuillez les corriger avant de continuer.', RED);
    log('\n📝 Conseils:', YELLOW);
    log('1. Vérifiez les erreurs TypeScript ci-dessus', YELLOW);
    log('2. Vérifiez les erreurs ESLint', YELLOW);
    log('3. Vérifiez que tous les exports sont corrects', YELLOW);
    log('4. Vérifiez les erreurs API dans la section 7', YELLOW);
    log('5. Consultez docs/workflow/ERROR_INVESTIGATION.md pour les bonnes pratiques', YELLOW);
    process.exit(1);
  } else if (hasWarnings) {
    log('⚠️  Des avertissements ont été détectés. Vérifiez-les avant de continuer.', YELLOW);
    process.exit(0); // Warnings ne bloquent pas
  }
}

main();
