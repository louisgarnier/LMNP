/**
 * InboxScreen - Écran "Boîte de réception" (étape 3, écran ①)
 *
 * Remplace l'ancien écran "Non classées". Liste les transactions non
 * classées de la propriété active avec une suggestion de catégorie et une
 * règle proposée (motif + type de match). L'utilisateur peut :
 *  - Valider : classe la transaction et crée la règle proposée (ou celle
 *    ajustée via "Modifier").
 *  - Modifier : ajuste catégorie / motif / portée avant de valider.
 *  - Tout valider : valide en masse toutes les suggestions non ambiguës.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { inboxAPI, categoriesAPI, InboxItem, Category } from '../api/client';
import { useProperty } from '@/contexts/PropertyContext';
import CategorySelector from '@/components/CategorySelector';

type MatchType = 'exact' | 'prefix' | 'contains';

interface EditState {
  categoryId: number | null;
  pattern: string;
  matchType: MatchType;
  global: boolean; // true = portée "tous les biens" (property_id: null)
}

export default function InboxScreen() {
  const { activeProperty } = useProperty();
  const [items, setItems] = useState<InboxItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [validatingAll, setValidatingAll] = useState(false);

  // Sélections en attente pour les items sans suggestion (category_id null)
  const [pendingCategory, setPendingCategory] = useState<Record<number, number | null>>({});
  // Item en cours d'édition (« Modifier »)
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editState, setEditState] = useState<EditState | null>(null);

  const categoryLabel = (categoryId: number | null): string | null => {
    if (categoryId === null) return null;
    const category = categories.find((c) => c.id === categoryId);
    return category ? category.label : null;
  };

  const loadInbox = async () => {
    if (!activeProperty || activeProperty.id <= 0) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [inboxItems, categoryList] = await Promise.all([
        inboxAPI.list(activeProperty.id),
        categoriesAPI.list(),
      ]);
      setItems(inboxItems);
      setCategories(categoryList);
    } catch (err: any) {
      console.error('[InboxScreen] loadInbox - Erreur:', err);
      setError(err.message || "Erreur lors du chargement de la boîte de réception");
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInbox();
  }, [activeProperty?.id]);

  const startEdit = (item: InboxItem) => {
    setEditingId(item.transaction_id);
    setEditState({
      categoryId: item.suggestion.category_id,
      pattern: item.proposed_rule.pattern,
      matchType: item.proposed_rule.match_type,
      global: false,
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditState(null);
  };

  const handleValidate = async (item: InboxItem) => {
    if (!activeProperty || activeProperty.id <= 0) return;

    const isEditing = editingId === item.transaction_id && editState;
    const categoryId = isEditing
      ? editState!.categoryId
      : item.suggestion.category_id ?? pendingCategory[item.transaction_id] ?? null;

    if (categoryId === null) {
      setError('Veuillez sélectionner une catégorie avant de valider.');
      return;
    }

    const rule = isEditing
      ? {
          pattern: editState!.pattern,
          match_type: editState!.matchType,
          property_id: editState!.global ? null : activeProperty.id,
        }
      : {
          pattern: item.proposed_rule.pattern,
          match_type: item.proposed_rule.match_type,
          property_id: activeProperty.id,
        };

    setSavingId(item.transaction_id);
    setError(null);
    try {
      await inboxAPI.validate({
        transaction_id: item.transaction_id,
        category_id: categoryId,
        rule,
      });
      cancelEdit();
      await loadInbox();
    } catch (err: any) {
      console.error('[InboxScreen] handleValidate - Erreur:', err);
      setError(err.message || 'Erreur lors de la validation de la transaction');
    } finally {
      setSavingId(null);
    }
  };

  const handleValidateAll = async () => {
    if (!activeProperty || activeProperty.id <= 0) return;
    setValidatingAll(true);
    setError(null);
    try {
      await inboxAPI.validateAll(activeProperty.id);
      await loadInbox();
    } catch (err: any) {
      console.error('[InboxScreen] handleValidateAll - Erreur:', err);
      setError(err.message || 'Erreur lors de la validation en masse');
    } finally {
      setValidatingAll(false);
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
        ⏳ Chargement de la boîte de réception...
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600, color: '#1a1a1a', margin: 0 }}>
          {items.length} opération{items.length !== 1 ? 's' : ''} à classer
          <span style={{ fontSize: '13px', fontWeight: 400, color: '#6b7280', marginLeft: '8px' }}>
            le système propose une catégorie, tu confirmes
          </span>
        </h2>
        <button
          onClick={handleValidateAll}
          disabled={validatingAll || items.length === 0}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: 550,
            backgroundColor: validatingAll || items.length === 0 ? '#ccc' : '#1e3a5f',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: validatingAll || items.length === 0 ? 'not-allowed' : 'pointer',
          }}
        >
          {validatingAll ? '⏳ Validation...' : 'Tout valider'}
        </button>
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

      {items.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
          Aucune transaction à classer.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', border: '1px solid #e5e5e5', borderRadius: '10px', overflow: 'hidden' }}>
          {items.map((item, index) => {
            const isEditing = editingId === item.transaction_id;
            const suggestedLabel = categoryLabel(item.suggestion.category_id);
            const hasSuggestion = item.suggestion.category_id !== null;
            const isSaving = savingId === item.transaction_id;
            const isNegative = item.montant < 0;

            return (
              <div
                key={item.transaction_id}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '92px 1fr auto',
                  gap: '16px',
                  alignItems: 'center',
                  padding: '13px 16px',
                  borderBottom: index === items.length - 1 ? 'none' : '1px solid #f3f4f6',
                }}
              >
                <div style={{ color: '#9ca3af', fontSize: '12.5px' }}>{item.date}</div>
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontFamily: 'ui-monospace, SF Mono, Menlo, Consolas, monospace',
                      fontSize: '12.5px',
                      color: '#1a1a1a',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {item.nom}
                  </div>
                  <div style={{ fontSize: '12.5px', color: isNegative ? '#b45309' : '#6b7280', marginTop: '3px' }}>
                    {isNegative ? '− ' : '+ '}
                    {Math.abs(item.montant).toFixed(2)} €
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                  {isEditing && editState ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <input
                        type="text"
                        value={editState.pattern}
                        onChange={(e) => setEditState({ ...editState, pattern: e.target.value })}
                        style={{
                          padding: '6px 8px',
                          fontSize: '12.5px',
                          fontFamily: 'ui-monospace, SF Mono, Menlo, Consolas, monospace',
                          border: '1px solid #e5e5e5',
                          borderRadius: '4px',
                          minWidth: '160px',
                        }}
                      />
                      <select
                        value={editState.matchType}
                        onChange={(e) => setEditState({ ...editState, matchType: e.target.value as MatchType })}
                        style={{ padding: '6px 8px', fontSize: '13px', border: '1px solid #e5e5e5', borderRadius: '4px' }}
                      >
                        <option value="exact">exact</option>
                        <option value="prefix">préfixe</option>
                        <option value="contains">contient</option>
                      </select>
                      <CategorySelector
                        value={editState.categoryId}
                        onChange={(categoryId) => setEditState({ ...editState, categoryId })}
                      />
                      <select
                        value={editState.global ? 'global' : 'bien'}
                        onChange={(e) => setEditState({ ...editState, global: e.target.value === 'global' })}
                        style={{ padding: '6px 8px', fontSize: '13px', border: '1px solid #e5e5e5', borderRadius: '4px' }}
                      >
                        <option value="bien">ce bien</option>
                        <option value="global">tous les biens</option>
                      </select>
                    </div>
                  ) : hasSuggestion ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                      <span
                        style={{
                          backgroundColor: '#e7f4ec',
                          color: '#15803d',
                          fontSize: '12.5px',
                          fontWeight: 600,
                          padding: '4px 10px',
                          borderRadius: '7px',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {suggestedLabel}
                      </span>
                      <span style={{ fontSize: '11px', color: '#9ca3af' }}>suggéré</span>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                      <span
                        style={{
                          backgroundColor: '#fbf0e2',
                          color: '#b45309',
                          fontSize: '11px',
                          fontWeight: 600,
                          padding: '3px 8px',
                          borderRadius: '6px',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        aucune suggestion
                      </span>
                      <CategorySelector
                        value={pendingCategory[item.transaction_id] ?? null}
                        onChange={(categoryId) =>
                          setPendingCategory((prev) => ({ ...prev, [item.transaction_id]: categoryId }))
                        }
                      />
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '7px' }}>
                    <button
                      onClick={() => handleValidate(item)}
                      disabled={
                        isSaving ||
                        (!hasSuggestion && !isEditing && pendingCategory[item.transaction_id] == null) ||
                        (isEditing && editState?.categoryId == null)
                      }
                      style={{
                        padding: '5px 10px',
                        fontSize: '12.5px',
                        fontWeight: 550,
                        backgroundColor:
                          isSaving ||
                          (!hasSuggestion && !isEditing && pendingCategory[item.transaction_id] == null) ||
                          (isEditing && editState?.categoryId == null)
                            ? '#ccc'
                            : '#1e3a5f',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: isSaving ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {isSaving ? '⏳' : 'Valider'}
                    </button>
                    {hasSuggestion && !isEditing && (
                      <button
                        onClick={() => startEdit(item)}
                        style={{
                          padding: '5px 10px',
                          fontSize: '12.5px',
                          fontWeight: 550,
                          backgroundColor: 'transparent',
                          color: '#1a1a1a',
                          border: '1px solid #e5e5e5',
                          borderRadius: '8px',
                          cursor: 'pointer',
                        }}
                      >
                        Modifier
                      </button>
                    )}
                    {isEditing && (
                      <button
                        onClick={cancelEdit}
                        style={{
                          padding: '5px 10px',
                          fontSize: '12.5px',
                          fontWeight: 550,
                          backgroundColor: 'transparent',
                          color: '#6b7280',
                          border: '1px solid #e5e5e5',
                          borderRadius: '8px',
                          cursor: 'pointer',
                        }}
                      >
                        Annuler
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
