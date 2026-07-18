/**
 * Home page - Property selection
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 * Always check with the user before modifying this file.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useProperty } from '@/contexts/PropertyContext';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Ligne {
  poste: string;
  par_bien: Record<string, number> | null;
  app: number;
  liasse: number | null;
  ecart: number | null;
  ok: boolean | null;
}

interface AnneeRec {
  annee: number;
  brouillon: boolean;
  biens_inclus: number[];
  lignes: Ligne[];
  nb_ecarts: number;
}

interface RecResponse {
  annees: number[];
  results: Record<string, AnneeRec>;
}

function formatEuro(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v);
}

function euroColor(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '#5e6c84';
  if (v < 0) return '#bf2600';
  if (v > 0) return '#006644';
  return '#172b4d';
}

export default function HomePage() {
  const router = useRouter();
  const { activeProperty, properties, loading, error, setActiveProperty, createProperty, deleteProperty } = useProperty();
  const [isCreating, setIsCreating] = useState(false);
  const [newPropertyName, setNewPropertyName] = useState('');
  const [newPropertyAddress, setNewPropertyAddress] = useState('');
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; propertyId: number; propertyName: string } | null>(null);

  // Bloc fiscal global (section 2)
  const [recon, setRecon] = useState<RecResponse | null>(null);

  // Résultat {CY} par appartement (section 1)
  const [resultats, setResultats] = useState<Record<number, number | null>>({});

  const cy = recon && recon.annees.length > 0 ? Math.max(...recon.annees) : null;

  // Charge la réconciliation globale -> sert à déterminer l'exercice en cours (CY)
  // pour libeller le résultat des cartes appartement.
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE_URL}/api/reconciliation`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: RecResponse) => {
        if (!cancelled) setRecon(data);
      })
      .catch(() => { /* réconciliation indisponible -> cy null -> cartes en "—" */ });
    return () => {
      cancelled = true;
    };
  }, []);

  // Une fois CY connu, charge le résultat net réalisé de l'exercice en cours pour chaque appartement.
  const propertyIdsKey = properties.map((p) => p.id).join(',');
  useEffect(() => {
    if (cy === null || properties.length === 0) return;
    let cancelled = false;
    Promise.all(
      properties.map(async (p) => {
        try {
          const r = await fetch(`${API_BASE_URL}/api/compte-resultat/calculate?property_id=${p.id}&years=${cy}&realized=true`);
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const data = await r.json();
          const resultatNet = data?.results?.[String(cy)]?.resultat_net;
          return [p.id, typeof resultatNet === 'number' ? resultatNet : null] as const;
        } catch {
          return [p.id, null] as const;
        }
      })
    ).then((entries) => {
      if (!cancelled) setResultats(Object.fromEntries(entries));
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cy, propertyIdsKey]);

  const handleSelectProperty = (propertyId: number) => {
    const property = properties.find(p => p.id === propertyId);
    if (property) {
      setActiveProperty(property);
      router.push('/dashboard');
    }
  };

  const handleCreateProperty = async () => {
    if (!newPropertyName.trim()) {
      alert('Le nom de la propriété est requis');
      return;
    }

    try {
      setCreating(true);
      const newProperty = await createProperty(newPropertyName.trim(), newPropertyAddress.trim() || undefined);
      setActiveProperty(newProperty);
      setNewPropertyName('');
      setNewPropertyAddress('');
      setIsCreating(false);
    router.push('/dashboard');
    } catch (err: any) {
      console.error('Error creating property:', err);
      alert(err.message || 'Erreur lors de la création de la propriété');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProperty = async (propertyId: number, propertyName: string) => {
    const confirmMessage = `⚠️ ATTENTION : Suppression définitive\n\n` +
      `Êtes-vous sûr de vouloir supprimer la propriété "${propertyName}" ?\n\n` +
      `Cette action supprimera DÉFINITIVEMENT :\n` +
      `- Toutes les transactions\n` +
      `- Tous les mappings\n` +
      `- Tous les crédits et mensualités\n` +
      `- Tous les amortissements\n` +
      `- Tous les comptes de résultat\n` +
      `- Tous les bilans\n` +
      `- Toutes les configurations\n\n` +
      `Cette action est IRRÉVERSIBLE.`;

    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      setDeletingId(propertyId);
      setContextMenu(null); // Fermer le menu contextuel
      await deleteProperty(propertyId);

      // Si la propriété supprimée était la propriété active, la désélectionner
      if (activeProperty?.id === propertyId) {
        setActiveProperty(null);
      }
    } catch (err: any) {
      console.error('Error deleting property:', err);
      alert(err.message || 'Erreur lors de la suppression de la propriété');
    } finally {
      setDeletingId(null);
    }
  };

  const handleContextMenu = (e: React.MouseEvent, propertyId: number, propertyName: string) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      propertyId,
      propertyName,
    });
  };

  const closeContextMenu = () => {
    setContextMenu(null);
  };

  // Fermer le menu contextuel si on clique ailleurs
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu) {
        closeContextMenu();
      }
    };

    if (contextMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => {
        document.removeEventListener('click', handleClickOutside);
      };
    }
  }, [contextMenu]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#6b7280' }}>Chargement des propriétés...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb' }}>
        <div style={{ textAlign: 'center', color: '#dc2626', maxWidth: '600px', padding: '20px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '16px' }}>Erreur de chargement</h2>
          <p style={{ marginBottom: '16px' }}>{error}</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              cursor: 'pointer',
              fontWeight: '500',
            }}
          >
            Recharger la page
          </button>
          <p style={{ marginTop: '16px', fontSize: '14px', color: '#6b7280' }}>
            Vérifiez que le serveur backend est démarré sur http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f4f5f7', color: '#172b4d' }}>
      <div style={{ backgroundColor: '#fff', borderBottom: '1px solid #dfe1e6', padding: '16px 0', marginBottom: '24px' }}>
        <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '0 20px' }}>
          <div style={{ fontSize: '17px', fontWeight: 700, color: '#172b4d' }}>LMNP — Gestion comptable</div>
          <div style={{ fontSize: '12px', color: '#5e6c84', marginTop: '2px' }}>
            {cy !== null ? `Exercice en cours ${cy}` : 'Sélectionnez ou créez un appartement pour commencer'}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '0 20px 60px' }}>

        {/* ═══════════ SECTION 1 : APPARTEMENTS ═══════════ */}
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#172b4d' }}>Appartements</div>
            <div style={{ fontSize: '12px', color: '#5e6c84', marginTop: '2px' }}>
              Cliquez un appartement pour entrer dans son espace (transactions, amortissements…)
            </div>
          </div>
          <div
            style={{ fontSize: '12px', color: '#0052cc', cursor: 'pointer' }}
            onClick={() => setIsCreating(true)}
          >
            + Ajouter un appartement
          </div>
        </div>

        {!isCreating ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px', marginBottom: '34px' }}>
            {properties.map((property) => (
              <div
                key={property.id}
                style={{
                  backgroundColor: '#fff',
                  border: '1px solid #dfe1e6',
                  borderRadius: '8px',
                  padding: '14px',
                  cursor: 'pointer',
                  transition: 'box-shadow .12s',
                  position: 'relative',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(9,30,66,.12)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                }}
                onContextMenu={(e) => handleContextMenu(e, property.id, property.name)}
                onClick={() => handleSelectProperty(property.id)}
              >
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#172b4d' }}>{property.name}</div>
                {property.address && (
                  <div style={{ fontSize: '12px', color: '#5e6c84', marginTop: '2px' }}>{property.address}</div>
                )}
                <div style={{ borderTop: '1px solid #f4f5f7', margin: '10px 0' }} />
                {/* TODO V2: solde depuis la banque */}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <span style={{ color: '#5e6c84' }}>Résultat {cy ?? '—'}</span>
                  <span style={{ color: euroColor(resultats[property.id]), fontWeight: 600 }}>
                    {property.id in resultats ? formatEuro(resultats[property.id]) : '—'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ maxWidth: '500px', margin: '0 auto 34px', backgroundColor: 'white', border: '1px solid #dfe1e6', borderRadius: '8px', padding: '32px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937', marginBottom: '24px' }}>
              Créer une nouvelle propriété
            </h2>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '8px' }}>
                Nom de la propriété *
              </label>
              <input
                type="text"
                value={newPropertyName}
                onChange={(e) => setNewPropertyName(e.target.value)}
                placeholder="Ex: Appartement 1"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                }}
                autoFocus
              />
            </div>
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '8px' }}>
                Adresse (optionnel)
              </label>
              <input
                type="text"
                value={newPropertyAddress}
                onChange={(e) => setNewPropertyAddress(e.target.value)}
                placeholder="Ex: 123 Rue de Test, 75001 Paris"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={handleCreateProperty}
                disabled={creating || !newPropertyName.trim()}
                style={{
                  flex: 1,
                  backgroundColor: creating || !newPropertyName.trim() ? '#9ca3af' : '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: creating || !newPropertyName.trim() ? 'not-allowed' : 'pointer',
                }}
              >
                {creating ? 'Création...' : 'Créer'}
              </button>
              <button
                onClick={() => {
                  setIsCreating(false);
                  setNewPropertyName('');
                  setNewPropertyAddress('');
                }}
                disabled={creating}
                style={{
                  flex: 1,
                  backgroundColor: 'white',
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: creating ? 'not-allowed' : 'pointer',
                }}
              >
                Annuler
              </button>
            </div>
          </div>
        )}

        {/* Menu contextuel */}
        {contextMenu && (
          <div
            style={{
              position: 'fixed',
              top: contextMenu.y,
              left: contextMenu.x,
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
              zIndex: 1000,
              minWidth: '200px',
              padding: '4px 0',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => handleDeleteProperty(contextMenu.propertyId, contextMenu.propertyName)}
              disabled={deletingId === contextMenu.propertyId}
              style={{
                width: '100%',
                padding: '12px 16px',
                textAlign: 'left',
                border: 'none',
                backgroundColor: 'transparent',
                color: deletingId === contextMenu.propertyId ? '#9ca3af' : '#dc2626',
                cursor: deletingId === contextMenu.propertyId ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => {
                if (deletingId !== contextMenu.propertyId) {
                  e.currentTarget.style.backgroundColor = '#fef2f2';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              {deletingId === contextMenu.propertyId ? 'Suppression...' : '🗑️ Supprimer'}
            </button>
          </div>
        )}

        {/* ═══════════ SECTION 2 : LIASSE FISCALE / DONNÉES GLOBALES ═══════════ */}
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#172b4d' }}>Liasse fiscale · données globales</div>
            <div style={{ fontSize: '12px', color: '#5e6c84', marginTop: '2px' }}>
              Tous appartements confondus — hors du contexte d'un appartement. C'est ici que vit la fiscalité.
            </div>
          </div>
          <span style={{ fontSize: '12px', color: '#0052cc', cursor: 'pointer' }}>
            Charger une liasse
          </span>
        </div>

        {/* Entrée principale : Vision globale */}
        <Link
          href="/dashboard/liasse-fiscale"
          style={{
            display: 'block',
            backgroundColor: '#fff',
            border: '1px solid #dfe1e6',
            borderLeft: '3px solid #0052cc',
            borderRadius: '8px',
            padding: '16px 18px',
            cursor: 'pointer',
            textDecoration: 'none',
            marginBottom: '12px',
            transition: 'box-shadow .12s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 2px 8px rgba(9,30,66,.12)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
        >
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#172b4d' }}>Vision globale →</div>
          <div style={{ fontSize: '12px', color: '#5e6c84', marginTop: '4px', lineHeight: 1.5 }}>
            Résultat par appartement + entité, les deux tirelires (déficit &amp; amortissements reportés), et le choix d&apos;imputation par année.
          </div>
        </Link>

        {/* Deux vues secondaires */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
          {[
            { title: 'Voir le détail par appartement →', desc: 'Compte de résultat groupé par appartement, comparé à la liasse déposée, par exercice.', href: '/dashboard/liasse-fiscale/detail' },
            { title: 'Voir la chaîne fiscale année par année →', desc: 'Résultat comptable → résultat fiscal → déficit & amortissements reportés. App vs Officiel.', href: '/dashboard/liasse-fiscale/chaine' },
          ].map((entry) => (
            <Link
              key={entry.href}
              href={entry.href}
              style={{
                display: 'block',
                backgroundColor: '#fff',
                border: '1px solid #dfe1e6',
                borderRadius: '8px',
                padding: '14px 16px',
                cursor: 'pointer',
                textDecoration: 'none',
                transition: 'box-shadow .12s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 2px 8px rgba(9,30,66,.12)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
            >
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#172b4d' }}>{entry.title}</div>
              <div style={{ fontSize: '11px', color: '#5e6c84', marginTop: '3px', lineHeight: 1.45 }}>{entry.desc}</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
