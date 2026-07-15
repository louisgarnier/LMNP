/**
 * ParametresScreen — Onglet « Paramètres » (étape 5, connexion Enable Banking)
 *
 * Trois blocs :
 *  - Statut du connecteur (mode réel / démo).
 *  - Connecter une banque : liste des ASPSP, un clic démarre le flux OAuth
 *    (redirection vers `authorization_url`).
 *  - Retour automatique : au montage, si l'URL contient
 *    `?eb_callback=1&code=...&state=...` (redirection Enable Banking), on
 *    échange le code contre une session + la liste des comptes disponibles,
 *    et l'utilisateur en sélectionne UN à rattacher à la propriété active.
 *
 * La carte détaillée par compte connecté (solde, dernière synchro, bouton
 * synchroniser, alerte J-30 avant expiration de session) est la Task 8 —
 * volontairement pas construite ici.
 */

'use client';

import React, { useEffect, useState } from 'react';
import { bankingAPI, BankingStatus, Aspsp, BankingAccountPreview } from '../api/client';
import { useProperty } from '@/contexts/PropertyContext';

// Persiste le nom de la banque choisie le temps de l'aller-retour OAuth
// (le retour Enable Banking ne renvoie que `code` + `state`, jamais le nom
// de la banque — on le retrouve via ce state côté navigateur).
const PENDING_KEY = 'eb_pending_connect';

type PendingConnect = { state: string; aspsp_name: string };

export default function ParametresScreen() {
  const { activeProperty } = useProperty();
  const propertyId = activeProperty?.id ?? null;

  const [status, setStatus] = useState<BankingStatus | null>(null);
  const [aspsps, setAspsps] = useState<Aspsp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectingName, setConnectingName] = useState<string | null>(null);

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

  // Retour automatique depuis Enable Banking : ?eb_callback=1&code=...&state=...
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('eb_callback') !== '1') return;
    const code = params.get('code');
    const state = params.get('state');

    // Nettoyer l'URL tout de suite pour éviter un rejeu du code au refresh.
    window.history.replaceState({}, '', `${window.location.pathname}?tab=parametres`);

    if (!code || !state) return;

    let alive = true;
    setCallbackProcessing(true);
    setError(null);
    (async () => {
      try {
        const res = await bankingAPI.createSession({ code, state });
        if (!alive) return;

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
        if (alive) {
          console.error('[ParametresScreen] createSession - Erreur:', err);
          setError(err.message || 'Erreur lors de la récupération des comptes');
        }
      } finally {
        if (alive) setCallbackProcessing(false);
        try {
          window.sessionStorage.removeItem(PENDING_KEY);
        } catch {
          // ignore
        }
      }
    })();
    return () => {
      alive = false;
    };
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
    } catch (err: any) {
      console.error('[ParametresScreen] handleSelectAccount - Erreur:', err);
      setError(err.message || 'Erreur lors du rattachement du compte');
    } finally {
      setSelecting(false);
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
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {aspsps.map((b) => (
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
        )}
      </div>
    </div>
  );
}
