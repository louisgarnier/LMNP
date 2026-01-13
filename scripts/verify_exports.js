/**
 * Script de vérification des exports TypeScript/JavaScript
 * Vérifie que tous les exports utilisés dans les composants existent bien dans les modules
 * 
 * Usage: node scripts/verify_exports.js
 */

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.join(__dirname, '..');
const FRONTEND_SRC = path.join(PROJECT_ROOT, 'frontend', 'src');

// Couleurs pour la console
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function error(message) {
  log(`❌ ${message}`, 'red');
}

function success(message) {
  log(`✅ ${message}`, 'green');
}

function warning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

function info(message) {
  log(`ℹ️  ${message}`, 'blue');
}

// Extraire les imports depuis un fichier
function extractImports(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const imports = [];
  
  // Pattern pour détecter les imports: import { ... } from '...'
  const importRegex = /import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['"]([^'"]+)['"]/g;
  let match;
  
  while ((match = importRegex.exec(content)) !== null) {
    const namedImports = match[1] || '';
    const defaultImport = match[2] || '';
    const modulePath = match[3];
    
    if (namedImports) {
      // Parser les imports nommés: { a, b, c }
      const importsList = namedImports.split(',').map(i => i.trim());
      imports.push({
        type: 'named',
        imports: importsList,
        from: modulePath,
      });
    }
    
    if (defaultImport) {
      imports.push({
        type: 'default',
        imports: [defaultImport],
        from: modulePath,
      });
    }
  }
  
  return imports;
}

// Extraire les exports depuis un fichier
function extractExports(filePath) {
  if (!fs.existsSync(filePath)) {
    return { named: [], default: [] };
  }
  
  const content = fs.readFileSync(filePath, 'utf-8');
  const exports = { named: [], default: [] };
  
  // Exports nommés: export const/function/interface/type X
  const namedExportRegex = /export\s+(?:const|function|interface|type|class|enum)\s+(\w+)/g;
  let match;
  while ((match = namedExportRegex.exec(content)) !== null) {
    exports.named.push(match[1]);
  }
  
  // Export default: export default
  if (/export\s+default/.test(content)) {
    exports.default.push('default');
  }
  
  // Export { ... } from '...'
  const reExportRegex = /export\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]/g;
  while ((match = reExportRegex.exec(content)) !== null) {
    const exportsList = match[1].split(',').map(e => e.trim().split(' as ')[0]);
    exports.named.push(...exportsList);
  }
  
  return exports;
}

// Résoudre le chemin d'un module
function resolveModulePath(importPath, fromFile) {
  // Si c'est un alias @/, résoudre depuis src/
  if (importPath.startsWith('@/')) {
    const relativePath = importPath.replace('@/', '');
    return path.join(FRONTEND_SRC, relativePath);
  }
  
  // Si c'est un chemin relatif
  if (importPath.startsWith('.')) {
    const dir = path.dirname(fromFile);
    return path.resolve(dir, importPath);
  }
  
  // Sinon, c'est un module npm (on ne vérifie pas)
  return null;
}

// Vérifier un fichier
function verifyFile(filePath) {
  const imports = extractImports(filePath);
  const issues = [];
  
  for (const imp of imports) {
    const modulePath = resolveModulePath(imp.from, filePath);
    
    if (!modulePath) {
      // Module npm, on skip
      continue;
    }
    
    // Ajouter l'extension .ts ou .tsx si nécessaire
    let actualPath = modulePath;
    if (!fs.existsSync(actualPath)) {
      if (fs.existsSync(actualPath + '.ts')) {
        actualPath = actualPath + '.ts';
      } else if (fs.existsSync(actualPath + '.tsx')) {
        actualPath = actualPath + '.tsx';
      } else {
        issues.push({
          file: filePath,
          import: imp,
          error: `Module not found: ${imp.from} (resolved to ${modulePath})`,
        });
        continue;
      }
    }
    
    const exports = extractExports(actualPath);
    
    for (const importedName of imp.imports) {
      if (imp.type === 'default') {
        if (!exports.default.includes('default')) {
          issues.push({
            file: filePath,
            import: imp,
            error: `Default export not found in ${imp.from}`,
          });
        }
      } else {
        if (!exports.named.includes(importedName)) {
          issues.push({
            file: filePath,
            import: imp,
            error: `Named export '${importedName}' not found in ${imp.from}`,
            available: exports.named.slice(0, 10), // Afficher les 10 premiers exports disponibles
          });
        }
      }
    }
  }
  
  return issues;
}

// Trouver tous les fichiers .tsx et .ts dans src/
function findSourceFiles(dir) {
  const files = [];
  
  function walk(currentDir) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);
      
      if (entry.isDirectory()) {
        // Ignorer node_modules et .next
        if (entry.name !== 'node_modules' && entry.name !== '.next' && entry.name !== '__pycache__') {
          walk(fullPath);
        }
      } else if (entry.isFile() && (entry.name.endsWith('.tsx') || entry.name.endsWith('.ts'))) {
        files.push(fullPath);
      }
    }
  }
  
  walk(dir);
  return files;
}

// Main
function main() {
  log('\n🔍 Vérification des exports TypeScript/JavaScript\n', 'blue');
  
  const sourceFiles = findSourceFiles(FRONTEND_SRC);
  info(`Analyse de ${sourceFiles.length} fichiers...\n`);
  
  let totalIssues = 0;
  const issuesByFile = {};
  
  for (const file of sourceFiles) {
    const issues = verifyFile(file);
    if (issues.length > 0) {
      issuesByFile[file] = issues;
      totalIssues += issues.length;
    }
  }
  
  if (totalIssues === 0) {
    success('Aucun problème détecté ! Tous les exports sont valides.\n');
    process.exit(0);
  } else {
    error(`\n${totalIssues} problème(s) détecté(s) :\n`);
    
    for (const [file, issues] of Object.entries(issuesByFile)) {
      const relativePath = path.relative(PROJECT_ROOT, file);
      error(`\n📄 ${relativePath}:`);
      
      for (const issue of issues) {
        error(`   - ${issue.error}`);
        if (issue.available && issue.available.length > 0) {
          warning(`     Exports disponibles: ${issue.available.join(', ')}${issue.available.length > 10 ? '...' : ''}`);
        }
      }
    }
    
    log('\n', 'reset');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { verifyFile, extractExports, extractImports };
