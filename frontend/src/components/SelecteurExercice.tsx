/**
 * Barre de sélection d'exercice, partagée par les onglets du module fiscal.
 *
 * Les exercices viennent de la chaîne — jamais d'une liste écrite en dur. Un
 * exercice sans liasse déposée (brouillon) est signalé en pointillés.
 *
 * ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
 */
'use client';

export default function SelecteurExercice({
  annees,
  actif,
  brouillons,
  onChange,
}: {
  annees: number[];
  actif: number;
  brouillons?: Set<number>;
  onChange: (annee: number) => void;
}) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
      <span style={{ fontSize: 12, color: '#5e6c84', marginRight: 4 }}>Exercice :</span>
      {[...annees].sort((a, b) => a - b).map((a) => {
        const on = a === actif;
        const draft = brouillons?.has(a);
        return (
          <button
            key={a}
            onClick={() => onChange(a)}
            title={draft ? 'Aucune liasse déposée pour cet exercice' : undefined}
            style={{
              fontSize: 12.5,
              padding: '4px 11px',
              borderRadius: 4,
              cursor: 'pointer',
              background: on ? '#1e3a5f' : '#fff',
              color: on ? '#fff' : '#5e6c84',
              border: `1px ${draft ? 'dashed' : 'solid'} ${on ? '#1e3a5f' : '#dfe1e6'}`,
              fontWeight: on ? 600 : 400,
            }}
          >
            {a}
          </button>
        );
      })}
    </div>
  );
}
