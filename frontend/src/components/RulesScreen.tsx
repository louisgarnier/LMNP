/**
 * RulesScreen - Écran "Règles" (étape 3, écran ②)
 *
 * Remplace l'ancien écran "Mapping". Table unique des règles de
 * classification automatique pour la propriété active (règles propres au
 * bien + règles globales). Permet de créer une règle avec préversion live
 * (rulesAPI.preview) et de supprimer une règle existante (rulesAPI.remove
 * ne déclasse pas l'historique : c'est un comportement backend, l'UI se
 * contente de retirer la règle et de recharger).
 */

'use client';

import React, { useState, useEffect } from 'react';
import { rulesAPI, categoriesAPI, Rule, Category, RuleInput } from '../api/client';
import { useProperty } from '@/contexts/PropertyContext';
import CategorySelector from '@/components/CategorySelector';

type MatchType = 'exact' | 'prefix' | 'contains';

const MATCH_TYPE_LABELS: Record<MatchType, string> = {
  exact: 'exact',
  prefix: 'préfixe',
  contains: 'contient',
};

const SOURCE_LABELS: Record<string, string> = {
  migrated: 'migrée',
  manual: 'manuelle',
  inbox: 'inbox',
};

interface NewRuleState {
  pattern: string;
  matchType: MatchType;
  categoryId: number | null;
  global: boolean; // true = portée "tous les biens" (property_id: null)
  applyToExisting: boolean;
}

const EMPTY_NEW_RULE: NewRuleState = {
  pattern: '',
  matchType: 'prefix',
  categoryId: null,
  global: false,
  applyToExisting: false,
};

export default function RulesScreen() {
  const { activeProperty } = useProperty();
  const [rules, setRules] = useState<Rule[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const [newRule, setNewRule] = useState<NewRuleState>(EMPTY_NEW_RULE);
  const [preview, setPreview] = useState<{ would_classify: number; conflicts: { transaction_id: number; current_category_id: number }[] } | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const categoryLabel = (categoryId: number): string => {
    const category = categories.find((c) => c.id === categoryId);
    return category ? category.label : `#${categoryId}`;
  };

  const loadRules = async () => {
    if (!activeProperty || activeProperty.id <= 0) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [ruleList, categoryList] = await Promise.all([
        rulesAPI.list(activeProperty.id),
        categoriesAPI.list(),
      ]);
      setRules(ruleList);
      setCategories(categoryList);
    } catch (err: any) {
      console.error('[RulesScreen] loadRules - Erreur:', err);
      setError(err.message || 'Erreur lors du chargement des règles');
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeProperty?.id]);

  // Préversion live : à chaque changement des champs motif/type/catégorie/portée,
  // on interroge rulesAPI.preview (sans créer la règle).
  useEffect(() => {
    if (!activeProperty || activeProperty.id <= 0) return;
    if (!newRule.pattern.trim() || newRule.categoryId === null) {
      setPreview(null);
      return;
    }

    let cancelled = false;
    const ruleInput: RuleInput = {
      pattern: newRule.pattern.trim(),
      match_type: newRule.matchType,
      category_id: newRule.categoryId,
      property_id: newRule.global ? null : activeProperty.id,
    };

    setPreviewLoading(true);
    const handle = setTimeout(async () => {
      try {
        const result = await rulesAPI.preview(activeProperty.id, ruleInput);
        if (!cancelled) {
          setPreview(result);
        }
      } catch (err: any) {
        console.error('[RulesScreen] preview - Erreur:', err);
        if (!cancelled) {
          setError(err.message || 'Erreur lors de la préversion de la règle');
          setPreview(null);
        }
      } finally {
        if (!cancelled) {
          setPreviewLoading(false);
        }
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(handle);
    };
  }, [newRule.pattern, newRule.matchType, newRule.categoryId, newRule.global, activeProperty?.id]);

  const handleCreate = async () => {
    if (!activeProperty || activeProperty.id <= 0) return;
    if (!newRule.pattern.trim() || newRule.categoryId === null) {
      setError('Veuillez renseigner un motif et une catégorie avant de créer la règle.');
      return;
    }

    setCreating(true);
    setError(null);
    try {
      await rulesAPI.create(activeProperty.id, {
        pattern: newRule.pattern.trim(),
        match_type: newRule.matchType,
        category_id: newRule.categoryId,
        property_id: newRule.global ? null : activeProperty.id,
      });
      setNewRule(EMPTY_NEW_RULE);
      setPreview(null);
      await loadRules();
    } catch (err: any) {
      console.error('[RulesScreen] handleCreate - Erreur:', err);
      setError(err.message || 'Erreur lors de la création de la règle');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette règle ? Les transactions déjà classées ne seront pas déclassées.')) {
      return;
    }
    setDeletingId(id);
    setError(null);
    try {
      await rulesAPI.remove(id);
      await loadRules();
    } catch (err: any) {
      console.error('[RulesScreen] handleDelete - Erreur:', err);
      setError(err.message || 'Erreur lors de la suppression de la règle');
    } finally {
      setDeletingId(null);
    }
  };

  if (!activeProperty || activeProperty.id <= 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        Aucune propriété sélectionnée
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        ⏳ Chargement des règles...
      </div>
    );
  }

  const globalCount = rules.filter((r) => r.property_id === null).length;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600, color: '#1a1a1a', margin: 0 }}>
          {rules.length} règle{rules.length !== 1 ? 's' : ''}
          <span style={{ fontSize: '13px', fontWeight: 400, color: '#6b7280', marginLeft: '8px' }}>
            dont {globalCount} globale{globalCount !== 1 ? 's' : ''} (tous les biens)
          </span>
        </h2>
      </div>

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

      {rules.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
          Aucune règle pour cette propriété.
        </div>
      ) : (
        <div style={{ border: '1px solid #e5e5e5', borderRadius: '10px', overflowX: 'auto' }}>
          <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: '720px' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#9ca3af', padding: '10px 14px', borderBottom: '1px solid #e5e5e5', backgroundColor: '#eef0f3' }}>Motif</th>
                <th style={{ textAlign: 'left', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#9ca3af', padding: '10px 14px', borderBottom: '1px solid #e5e5e5', backgroundColor: '#eef0f3' }}>Type de match</th>
                <th style={{ textAlign: 'left', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#9ca3af', padding: '10px 14px', borderBottom: '1px solid #e5e5e5', backgroundColor: '#eef0f3' }}>Catégorie</th>
                <th style={{ textAlign: 'left', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#9ca3af', padding: '10px 14px', borderBottom: '1px solid #e5e5e5', backgroundColor: '#eef0f3' }}>Portée</th>
                <th style={{ textAlign: 'right', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#9ca3af', padding: '10px 14px', borderBottom: '1px solid #e5e5e5', backgroundColor: '#eef0f3' }}>Opérations</th>
                <th style={{ textAlign: 'left', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#9ca3af', padding: '10px 14px', borderBottom: '1px solid #e5e5e5', backgroundColor: '#eef0f3' }}>Source</th>
                <th style={{ padding: '10px 14px', borderBottom: '1px solid #e5e5e5', backgroundColor: '#eef0f3' }}></th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id}>
                  <td style={{ padding: '11px 14px', borderBottom: '1px solid #f3f4f6', fontFamily: 'ui-monospace, SF Mono, Menlo, Consolas, monospace', fontSize: '12.5px', color: '#1a1a1a' }}>
                    {rule.pattern}
                    {rule.strict_ratio === false && (
                      <span style={{ fontSize: '10.5px', color: '#9ca3af', display: 'block', marginTop: '3px' }}>
                        garde 70 % désactivée
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '11px 14px', borderBottom: '1px solid #f3f4f6', fontSize: '13px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', fontSize: '11.5px', fontWeight: 600, padding: '3px 9px', borderRadius: '20px', backgroundColor: '#f3f5f8', color: '#6b7280' }}>
                      {MATCH_TYPE_LABELS[rule.match_type]}
                    </span>
                  </td>
                  <td style={{ padding: '11px 14px', borderBottom: '1px solid #f3f4f6', fontSize: '13px', color: '#1a1a1a', fontWeight: 550 }}>
                    {categoryLabel(rule.category_id)}
                  </td>
                  <td style={{ padding: '11px 14px', borderBottom: '1px solid #f3f4f6', fontSize: '13px' }}>
                    {rule.property_id === null ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', fontSize: '11.5px', fontWeight: 600, padding: '3px 9px', borderRadius: '20px', backgroundColor: '#fbf0e2', color: '#b45309' }}>
                        tous les biens
                      </span>
                    ) : (
                      <span style={{ display: 'inline-flex', alignItems: 'center', fontSize: '11.5px', fontWeight: 600, padding: '3px 9px', borderRadius: '20px', backgroundColor: '#eaf0f6', color: '#1e3a5f' }}>
                        ce bien
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '11px 14px', borderBottom: '1px solid #f3f4f6', fontSize: '13px', textAlign: 'right', color: '#6b7280', fontVariantNumeric: 'tabular-nums' }}>
                    {rule.tx_count ?? 0}
                  </td>
                  <td style={{ padding: '11px 14px', borderBottom: '1px solid #f3f4f6', fontSize: '13px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', fontSize: '11.5px', fontWeight: 500, padding: '3px 9px', borderRadius: '20px', backgroundColor: '#f3f5f8', color: '#9ca3af' }}>
                      {SOURCE_LABELS[rule.source] || rule.source}
                    </span>
                  </td>
                  <td style={{ padding: '11px 14px', borderBottom: '1px solid #f3f4f6', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                      <button
                        disabled
                        title="Modifier (bientôt disponible)"
                        style={{ width: '28px', height: '28px', borderRadius: '7px', border: '1px solid #e5e5e5', backgroundColor: 'white', color: '#6b7280', cursor: 'not-allowed', fontSize: '14px' }}
                      >
                        ✎
                      </button>
                      <button
                        onClick={() => handleDelete(rule.id)}
                        disabled={deletingId === rule.id}
                        title="Supprimer"
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '7px',
                          border: '1px solid #e5e5e5',
                          backgroundColor: 'white',
                          color: '#6b7280',
                          cursor: deletingId === rule.id ? 'not-allowed' : 'pointer',
                          fontSize: '14px',
                        }}
                      >
                        {deletingId === rule.id ? '⏳' : '🗑'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: '14px', border: '1px dashed #1e3a5f', borderRadius: '10px', backgroundColor: '#eaf0f6', padding: '14px 16px' }}>
        <div style={{ fontSize: '12.5px', fontWeight: 650, color: '#1e3a5f', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
          Nouvelle règle — préversion en direct
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontSize: '11px', color: '#6b7280', fontWeight: 600 }}>Motif</label>
            <input
              type="text"
              value={newRule.pattern}
              onChange={(e) => setNewRule({ ...newRule, pattern: e.target.value })}
              placeholder="CB CASTORAMA"
              style={{
                border: '1px solid #e5e5e5',
                borderRadius: '7px',
                padding: '7px 11px',
                backgroundColor: 'white',
                fontSize: '12.5px',
                color: '#1a1a1a',
                fontFamily: 'ui-monospace, SF Mono, Menlo, Consolas, monospace',
                minWidth: '220px',
              }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontSize: '11px', color: '#6b7280', fontWeight: 600 }}>Type</label>
            <select
              value={newRule.matchType}
              onChange={(e) => setNewRule({ ...newRule, matchType: e.target.value as MatchType })}
              style={{ border: '1px solid #e5e5e5', borderRadius: '7px', padding: '7px 11px', backgroundColor: 'white', fontSize: '12.5px', color: '#1a1a1a', minWidth: '140px' }}
            >
              <option value="exact">exact</option>
              <option value="prefix">préfixe</option>
              <option value="contains">contient</option>
            </select>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontSize: '11px', color: '#6b7280', fontWeight: 600 }}>Catégorie</label>
            <CategorySelector
              value={newRule.categoryId}
              onChange={(categoryId) => setNewRule({ ...newRule, categoryId })}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label style={{ fontSize: '11px', color: '#6b7280', fontWeight: 600 }}>Portée</label>
            <select
              value={newRule.global ? 'global' : 'bien'}
              onChange={(e) => setNewRule({ ...newRule, global: e.target.value === 'global' })}
              style={{ border: '1px solid #e5e5e5', borderRadius: '7px', padding: '7px 11px', backgroundColor: 'white', fontSize: '12.5px', color: '#1a1a1a', minWidth: '160px' }}
            >
              <option value="bien">ce bien</option>
              <option value="global">tous les biens</option>
            </select>
          </div>
          <button
            onClick={handleCreate}
            disabled={creating || !newRule.pattern.trim() || newRule.categoryId === null}
            style={{
              marginLeft: 'auto',
              padding: '7px 13px',
              fontSize: '13px',
              fontWeight: 550,
              backgroundColor: creating || !newRule.pattern.trim() || newRule.categoryId === null ? '#ccc' : '#1e3a5f',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: creating || !newRule.pattern.trim() || newRule.categoryId === null ? 'not-allowed' : 'pointer',
            }}
          >
            {creating ? '⏳ Création...' : 'Créer la règle'}
          </button>
        </div>

        {(preview || previewLoading) && (
          <div style={{ marginTop: '13px', display: 'flex', gap: '18px', alignItems: 'center', flexWrap: 'wrap', paddingTop: '12px', borderTop: '1px solid #e5e5e5' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
              <b style={{ fontSize: '15px', fontVariantNumeric: 'tabular-nums', color: '#15803d' }}>
                {previewLoading ? '…' : preview?.would_classify ?? 0}
              </b>
              <span style={{ color: '#6b7280' }}>non classées seraient rangées</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
              <b style={{ fontSize: '15px', fontVariantNumeric: 'tabular-nums', color: '#b45309' }}>
                {previewLoading ? '…' : preview?.conflicts.length ?? 0}
              </b>
              <span style={{ color: '#6b7280' }}>en conflit avec des opérations déjà classées</span>
            </div>
            <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12.5px', color: '#6b7280', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={newRule.applyToExisting}
                onChange={(e) => setNewRule({ ...newRule, applyToExisting: e.target.checked })}
              />
              Appliquer aux opérations existantes <b style={{ color: '#1a1a1a' }}>(non par défaut)</b>
            </label>
          </div>
        )}
      </div>
    </div>
  );
}
