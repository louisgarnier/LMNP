/**
 * ParametresScreen — Onglet « Paramètres » (étape 5, connexion Enable Banking)
 *
 * Blocs :
 *  - Statut du connecteur (mode réel / démo).
 *  - Retour automatique : au montage, si l'URL contient
 *    `?eb_callback=1&code=...&state=...` (redirection Enable Banking), on
 *    échange le code contre une session + la liste des comptes disponibles,
 *    et l'utilisateur en sélectionne UN à rattacher à la propriété active.
 *  - Carte(s) compte(s) connecté(s) : nom, banque, IBAN masqué, solde banque,
 *    dernière synchro, échéance du consentement (bandeau orange + bouton
 *    renouveler si ≤ 30 jours), bouton Synchroniser (désactivé en mode démo —
 *    garde anti-pollution contre les fausses transactions mock) et bouton
 *    Déconnecter.
 *  - Connecter une banque : liste des ASPSP, un clic démarre le flux OAuth
 *    (redirection vers `authorization_url`).
 */

'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  bankingAPI,
  BankingStatus,
  Aspsp,
  BankingAccountPreview,
  BankingConnection,
  BankingSyncResult,
} from '../api/client';
import { useProperty } from '@/contexts/PropertyContext';

const CONSENT_WARNING_DAYS = 30;

/** Nombre de jours (arrondi au supérieur) entre maintenant et `dateStr` (peut être négatif si dépassé). */
function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const target = new Date(dateStr).getTime();
  if (Number.isNaN(target)) return null;
  return Math.ceil((target - Date.now()) / (24 * 60 * 60 * 1000));
}

function formatBalance(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return 'jamais';
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('fr-FR', { dateStyle: 'medium' });
}

// Persiste le nom de la banque choisie le temps de l'aller-retour OAuth
// (le retour Enable Banking ne renvoie que `code` + `state`, jamais le nom
// de la banque — on le retrouve via ce state côté navigateur).
const PENDING_KEY = 'eb_pending_connect';

type PendingConnect = { state: string; aspsp_name: string };

// Le retour de banque exige une adresse https publique (tunnel), mais l'échange
// du code doit se faire depuis l'origine locale : même origine que le clic de
// départ (donc le sessionStorage du nom de banque est retrouvé) et pas d'appel
// https→http bloqué par le navigateur. Si la page de retour est ouverte via le
// tunnel (host ≠ localhost), on rebondit vers localhost en gardant code+state.
// Retourne l'URL localhost cible, ou null si on est déjà en local.
export function localBounceTarget(
  hostname: string,
  pathname: string,
  search: string,
): string | null {
  if (hostname === 'localhost' || hostname === '127.0.0.1') return null;
  return `http://localhost:3000${pathname}${search}`;
}

// Enable Banking refuse d'enregistrer une URL de retour contenant des `?param`.
// On enregistre donc un chemin propre (/eb-callback) ; la banque y ajoute
// ?code=…&state=… au retour. Cette page reforme ensuite l'URL attendue par
// ParametresScreen (onglet Paramètres + eb_callback=1) sur l'origine locale.
// `search` = le query string reçu de la banque (ex "?code=A&state=B").
export function ebCallbackTarget(search: string): string {
  const bankParams = search.startsWith('?') ? search.slice(1) : search;
  const base =
    'http://localhost:3000/dashboard/transactions?tab=parametres&eb_callback=1';
  return bankParams ? `${base}&${bankParams}` : base;
}

export default function ParametresScreen() {
  const { activeProperty } = useProperty();
  const propertyId = activeProperty?.id ?? null;

  const [status, setStatus] = useState<BankingStatus | null>(null);
  const [aspsps, setAspsps] = useState<Aspsp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectingName, setConnectingName] = useState<string | null>(null);
  const [aspspFilter, setAspspFilter] = useState('');
  // Empêche le double-échange du code (StrictMode dev exécute l'effet 2×).
  const exchangeStartedRef = useRef(false);

  // Retour automatique : session en attente de sélection d'un compte.
  const [callbackProcessing, setCallbackProcessing] = useState(false);
  const [pendingSession, setPendingSession] = useState<{
    session_id: string;
    session_valid_until: string;
    property_id: number;
    aspsp_name: string;
  } | null>(null);
  const [availableAccounts, setAvailableAccounts] = useState<BankingAccountPreview[] | null>(null);
  const [selectedUid, setSelectedUid] = useState<string | null>(null);
  const [selecting, setSelecting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Comptes bancaires rattachés à la propriété active (Task 8).
  const [connections, setConnections] = useState<BankingConnection[]>([]);
  const [connectionsLoading, setConnectionsLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResults, setSyncResults] = useState<Record<string, BankingSyncResult> | null>(null);
  const [disconnectingId, setDisconnectingId] = useState<number | null>(null);

  const loadConnections = async () => {
    if (!propertyId || propertyId <= 0) return;
    setConnectionsLoading(true);
    try {
      const conns = await bankingAPI.connections(propertyId);
      setConnections(conns);
    } catch (err: any) {
      console.error('[ParametresScreen] loadConnections - Erreur:', err);
      setError(err.message || 'Erreur lors du chargement des comptes connectés');
    } finally {
      setConnectionsLoading(false);
    }
  };

  const loadStatusAndBanks = async () => {
    setLoading(true);
    setError(null);
    try {
      const [st, banks] = await Promise.all([bankingAPI.status(), bankingAPI.aspsps('FR')]);
      setStatus(st);
      setAspsps(banks);
    } catch (err: any) {
      console.error('[ParametresScreen] loadStatusAndBanks - Erreur:', err);
      setError(err.message || 'Erreur lors du chargement du statut de connexion bancaire');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatusAndBanks();
  }, []);

  useEffect(() => {
    loadConnections();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propertyId]);

  // Retour automatique depuis Enable Banking : ?eb_callback=1&code=...&state=...
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('eb_callback') !== '1') return;

    // Ouvert via le tunnel (host public) ? On rebondit vers localhost en gardant
    // code+state : l'échange se fera depuis l'origine locale (voir localBounceTarget).
    const bounce = localBounceTarget(
      window.location.hostname,
      window.location.pathname,
      window.location.search,
    );
    if (bounce) {
      window.location.replace(bounce);
      return;
    }

    const code = params.get('code');
    const state = params.get('state');

    // Nettoyer l'URL tout de suite pour éviter un rejeu du code au refresh.
    window.history.replaceState({}, '', `${window.location.pathname}?tab=parametres`);

    if (!code || !state) return;

    // Dédoublonnage : en dev, React (StrictMode) exécute l'effet DEUX fois.
    // Le code d'autorisation est à usage unique — on ne doit lancer l'échange
    // qu'une seule fois, et surtout NE PAS jeter son résultat (l'ancien garde
    // `alive=false` du cleanup StrictMode bloquait l'écran sur « Récupération… »).
    if (exchangeStartedRef.current) return;
    exchangeStartedRef.current = true;

    setCallbackProcessing(true);
    setError(null);
    (async () => {
      try {
        const res = await bankingAPI.createSession({ code, state });

        let aspspName = '';
        try {
          const raw = window.sessionStorage.getItem(PENDING_KEY);
          if (raw) {
            const pending: PendingConnect = JSON.parse(raw);
            if (pending.state === state) aspspName = pending.aspsp_name;
          }
        } catch {
          // sessionStorage indisponible : on continue sans le nom de banque.
        }

        setPendingSession({
          session_id: res.session_id,
          session_valid_until: res.session_valid_until,
          property_id: res.property_id,
          aspsp_name: aspspName,
        });
        setAvailableAccounts(res.accounts);
        setSelectedUid(res.accounts.length === 1 ? res.accounts[0].account_uid : null);
      } catch (err: any) {
        console.error('[ParametresScreen] createSession - Erreur:', err);
        setError(err.message || 'Erreur lors de la récupération des comptes');
      } finally {
        setCallbackProcessing(false);
        try {
          window.sessionStorage.removeItem(PENDING_KEY);
        } catch {
          // ignore
        }
      }
    })();
  }, []);

  const handleConnect = async (aspspName: string) => {
    if (!propertyId || propertyId <= 0) return;
    setConnectingName(aspspName);
    setError(null);
    try {
      const res = await bankingAPI.connect({ property_id: propertyId, aspsp_name: aspspName });
      try {
        window.sessionStorage.setItem(PENDING_KEY, JSON.stringify({ state: res.state, aspsp_name: aspspName }));
      } catch {
        // sessionStorage indisponible : le nom de banque sera manquant au retour.
      }
      window.location.href = res.authorization_url;
    } catch (err: any) {
      console.error('[ParametresScreen] handleConnect - Erreur:', err);
      setError(err.message || 'Erreur lors de la connexion à la banque');
      setConnectingName(null);
    }
  };

  const handleSelectAccount = async () => {
    if (!pendingSession || !availableAccounts || !selectedUid) return;
    const account = availableAccounts.find((a) => a.account_uid === selectedUid);
    if (!account) return;

    setSelecting(true);
    setError(null);
    try {
      await bankingAPI.selectAccount({
        property_id: pendingSession.property_id,
        account_uid: account.account_uid,
        session_id: pendingSession.session_id,
        session_valid_until: pendingSession.session_valid_until,
        aspsp_name: pendingSession.aspsp_name,
        account_name: account.name,
        iban_masked: account.iban_masked,
        currency: account.currency,
      });
      setSuccessMsg(`✅ Compte « ${account.name || account.iban_masked} » rattaché`);
      setPendingSession(null);
      setAvailableAccounts(null);
      setSelectedUid(null);
      await loadConnections();
    } catch (err: any) {
      console.error('[ParametresScreen] handleSelectAccount - Erreur:', err);
      setError(err.message || 'Erreur lors du rattachement du compte');
    } finally {
      setSelecting(false);
    }
  };

  const handleSync = async () => {
    if (!propertyId || propertyId <= 0) return;
    setSyncing(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const results = await bankingAPI.sync({ property_id: propertyId });
      setSyncResults(results);
      await loadConnections();
    } catch (err: any) {
      console.error('[ParametresScreen] handleSync - Erreur:', err);
      setError(err.message || 'Erreur lors de la synchronisation');
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async (accountId: number, label: string) => {
    if (!window.confirm(`Déconnecter le compte « ${label} » ? Les transactions déjà importées seront conservées.`)) {
      return;
    }
    setDisconnectingId(accountId);
    setError(null);
    try {
      await bankingAPI.disconnect(accountId);
      setSyncResults(null);
      await loadConnections();
    } catch (err: any) {
      console.error('[ParametresScreen] handleDisconnect - Erreur:', err);
      setError(err.message || 'Erreur lors de la déconnexion du compte');
    } finally {
      setDisconnectingId(null);
    }
  };

  if (!activeProperty || !propertyId || propertyId <= 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        Aucune propriété sélectionnée
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: 600, color: '#1a1a1a', margin: '0 0 24px' }}>
        Paramètres
        <span style={{ fontSize: '13px', fontWeight: 400, color: '#6b7280', marginLeft: '8px' }}>
          connexion bancaire (Enable Banking)
        </span>
      </h2>

      {error && (
        <div
          role="alert"
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#dc3545',
            fontSize: '14px',
          }}
        >
          ❌ {error}
        </div>
      )}

      {successMsg && (
        <div
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            backgroundColor: '#f0fdf4',
            border: '1px solid #86efac',
            borderRadius: '8px',
            color: '#15803d',
            fontSize: '14px',
          }}
        >
          {successMsg}
        </div>
      )}

      {/* Carte statut */}
      <div style={{ border: '1px solid #e5e5e5', borderRadius: '10px', padding: '16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <span style={{ fontSize: '15px', fontWeight: 600, color: '#1a1a1a' }}>Statut</span>
          {status && (
            <span
              style={{
                fontSize: '11px',
                fontWeight: 600,
                padding: '3px 8px',
                borderRadius: '6px',
                backgroundColor: status.live ? '#e7f4ec' : '#fbf0e2',
                color: status.live ? '#15803d' : '#b45309',
              }}
            >
              {status.live ? 'Connecté (mode réel)' : 'Mode démo'}
            </span>
          )}
        </div>
        <div style={{ fontSize: '13px', color: '#6b7280' }}>
          {loading ? 'Chargement…' : status?.message ?? '—'}
        </div>
      </div>

      {/* Retour automatique : sélection d'un compte parmi ceux disponibles */}
      {(callbackProcessing || availableAccounts) && (
        <div style={{ border: '1px solid #1e3a5f', borderRadius: '10px', padding: '16px', marginBottom: '16px' }}>
          <div style={{ fontSize: '15px', fontWeight: 600, color: '#1a1a1a', marginBottom: '10px' }}>
            Sélectionner un compte à rattacher
          </div>
          {callbackProcessing ? (
            <div style={{ color: '#6b7280', fontSize: '13px' }}>⏳ Récupération des comptes…</div>
          ) : availableAccounts && availableAccounts.length === 0 ? (
            <div style={{ color: '#6b7280', fontSize: '13px' }}>Aucun compte disponible pour cette connexion.</div>
          ) : (
            <>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '12px' }}>
                {availableAccounts?.map((a) => (
                  <label
                    key={a.account_uid}
                    style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', cursor: 'pointer' }}
                  >
                    <input
                      type="radio"
                      name="eb-account"
                      checked={selectedUid === a.account_uid}
                      onChange={() => setSelectedUid(a.account_uid)}
                    />
                    <span>
                      <b>{a.name || a.account_uid}</b>{' '}
                      <span style={{ color: '#6b7280' }}>
                        · {a.currency} · {a.iban_masked}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
              <button
                onClick={handleSelectAccount}
                disabled={selecting || !selectedUid}
                style={{
                  padding: '8px 16px',
                  fontSize: '13px',
                  fontWeight: 550,
                  backgroundColor: selecting || !selectedUid ? '#ccc' : '#1e3a5f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: selecting || !selectedUid ? 'not-allowed' : 'pointer',
                }}
              >
                {selecting ? '⏳ Rattachement…' : 'Rattacher ce compte'}
              </button>
            </>
          )}
        </div>
      )}

      {/* Carte(s) compte(s) connecté(s) */}
      {!connectionsLoading && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#1a1a1a' }}>Compte(s) connecté(s)</div>
            <button
              onClick={handleSync}
              disabled={syncing || !status?.live}
              style={{
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: 550,
                backgroundColor: syncing || !status?.live ? '#ccc' : '#1e3a5f',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: syncing || !status?.live ? 'not-allowed' : 'pointer',
              }}
            >
              {syncing ? '⏳ Synchronisation…' : 'Synchroniser'}
            </button>
          </div>

          {status?.live === false && (
            <div style={{ fontSize: '12px', color: '#b45309', marginBottom: '10px' }}>
              connecte tes credentials pour synchroniser
            </div>
          )}

          {syncResults && (
            <div
              role="alert"
              style={{
                padding: '10px 14px',
                marginBottom: '10px',
                backgroundColor: '#f0f9ff',
                border: '1px solid #bae6fd',
                borderRadius: '8px',
                fontSize: '13px',
                color: '#0c4a6e',
              }}
            >
              {Object.values(syncResults).map((r) => {
                const acc = connections.find((c) => c.id === r.account_id);
                return (
                  <div key={r.account_id} style={{ marginBottom: '4px' }}>
                    <b>{acc?.account_name ?? `Compte #${r.account_id}`}</b> : {r.inserted} nouvelle(s),{' '}
                    {r.deduplicated} déjà connue(s)
                    {r.errors.length > 0 && (
                      <span style={{ color: '#dc3545' }}> — ❌ {r.errors.join(' / ')}</span>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {connections.length === 0 ? (
            <div style={{ color: '#6b7280', fontSize: '13px' }}>Aucun compte connecté pour ce bien.</div>
          ) : (
            connections.map((c) => {
              const remaining = daysUntil(c.session_valid_until);
              const needsRenewal = remaining !== null && remaining <= CONSENT_WARNING_DAYS;
              return (
                <div
                  key={c.id}
                  style={{ border: '1px solid #e5e5e5', borderRadius: '10px', padding: '16px', marginBottom: '10px' }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '8px',
                    }}
                  >
                    <div style={{ fontSize: '14px', fontWeight: 600, color: '#1a1a1a' }}>
                      {c.account_name} <span style={{ color: '#6b7280', fontWeight: 400 }}>· {c.bank_name}</span>
                    </div>
                    <button
                      onClick={() => handleDisconnect(c.id, c.account_name || c.bank_name)}
                      disabled={disconnectingId === c.id}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        fontWeight: 550,
                        backgroundColor: 'white',
                        color: '#dc3545',
                        border: '1px solid #fecaca',
                        borderRadius: '8px',
                        cursor: disconnectingId === c.id ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {disconnectingId === c.id ? '⏳ Déconnexion…' : 'Déconnecter'}
                    </button>
                  </div>
                  <div
                    style={{
                      fontSize: '13px',
                      color: '#6b7280',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '2px',
                    }}
                  >
                    <span>IBAN : {c.iban_masked}</span>
                    <span>Solde banque : {formatBalance(c.bank_balance)}</span>
                    <span>Dernière synchro : {formatDateTime(c.last_sync_at)}</span>
                    <span>
                      Consentement valable jusqu'au {formatDate(c.session_valid_until)}
                      {remaining !== null && ` (${remaining >= 0 ? `${remaining} j` : 'expiré'})`}
                    </span>
                  </div>

                  {needsRenewal && (
                    <div
                      style={{
                        marginTop: '10px',
                        padding: '10px 12px',
                        backgroundColor: '#fbf0e2',
                        border: '1px solid #f5c98a',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '10px',
                        flexWrap: 'wrap',
                      }}
                    >
                      <span style={{ fontSize: '12px', color: '#b45309', fontWeight: 550 }}>
                        ⚠️ consentement à renouveler
                      </span>
                      <button
                        onClick={() => handleConnect(c.bank_name)}
                        disabled={connectingName === c.bank_name}
                        style={{
                          padding: '6px 12px',
                          fontSize: '12px',
                          fontWeight: 550,
                          backgroundColor: '#b45309',
                          color: 'white',
                          border: 'none',
                          borderRadius: '8px',
                          cursor: connectingName === c.bank_name ? 'not-allowed' : 'pointer',
                        }}
                      >
                        {connectingName === c.bank_name ? '⏳ Connexion…' : 'Renouveler'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Carte connecter une banque */}
      <div style={{ border: '1px solid #e5e5e5', borderRadius: '10px', padding: '16px' }}>
        <div style={{ fontSize: '15px', fontWeight: 600, color: '#1a1a1a', marginBottom: '10px' }}>
          Connecter une banque
        </div>
        {loading ? (
          <div style={{ color: '#6b7280', fontSize: '13px' }}>Chargement…</div>
        ) : aspsps.length === 0 ? (
          <div style={{ color: '#6b7280', fontSize: '13px' }}>Aucune banque disponible.</div>
        ) : (
          <>
          <input
            type="text"
            value={aspspFilter}
            onChange={(e) => setAspspFilter(e.target.value)}
            placeholder="🔍 Rechercher ta banque (ex : LCL, Crédit Mutuel…)"
            style={{
              width: '100%',
              padding: '8px 12px',
              fontSize: '13px',
              border: '1px solid #e5e5e5',
              borderRadius: '8px',
              marginBottom: '10px',
              boxSizing: 'border-box',
            }}
          />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {aspsps
              .filter((b) => b.name.toLowerCase().includes(aspspFilter.toLowerCase()))
              .map((b) => (
              <button
                key={b.name}
                onClick={() => handleConnect(b.name)}
                disabled={connectingName === b.name}
                style={{
                  padding: '8px 14px',
                  fontSize: '13px',
                  fontWeight: 550,
                  backgroundColor: 'white',
                  color: '#1a1a1a',
                  border: '1px solid #e5e5e5',
                  borderRadius: '8px',
                  cursor: connectingName === b.name ? 'not-allowed' : 'pointer',
                }}
              >
                {connectingName === b.name ? '⏳ Connexion…' : b.name}
              </button>
            ))}
          </div>
          </>
        )}
      </div>
    </div>
  );
}
