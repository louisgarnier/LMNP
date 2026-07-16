/**
 * Page de retour Enable Banking (chemin propre, sans query params à
 * l'enregistrement — Enable Banking les refuse). La banque renvoie ici avec
 * ?code=…&state=…, on rebascule vers l'onglet Paramètres sur l'origine locale
 * où toute la logique d'échange du code existe déjà (ParametresScreen).
 */

'use client';

import { useEffect } from 'react';
import { ebCallbackTarget } from '@/components/ParametresScreen';

export default function EbCallbackPage() {
  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.location.replace(ebCallbackTarget(window.location.search));
  }, []);

  return (
    <div style={{ padding: '48px', textAlign: 'center', color: '#6b7280' }}>
      <p>Connexion à ta banque en cours… redirection…</p>
    </div>
  );
}
