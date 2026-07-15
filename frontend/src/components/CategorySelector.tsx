/**
 * CategorySelector component - Sélecteur de catégorie partagé (Inbox, Règles)
 *
 * Charge le référentiel des catégories une fois via categoriesAPI.list()
 * et affiche un <select> natif groupé par group_label.
 */

'use client';

import { useEffect, useState } from 'react';
import { categoriesAPI, Category } from '@/api/client';

interface CategorySelectorProps {
  value: number | null;
  onChange: (categoryId: number | null) => void;
}

export default function CategorySelector({ value, onChange }: CategorySelectorProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const loadCategories = async () => {
      try {
        const items = await categoriesAPI.list();
        if (!cancelled) {
          setCategories(items);
        }
      } catch (error) {
        console.error('[CategorySelector] Erreur lors du chargement des catégories:', error);
        if (!cancelled) {
          setCategories([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadCategories();

    return () => {
      cancelled = true;
    };
  }, []);

  // Grouper les catégories par group_label en préservant l'ordre d'apparition
  const groups: { groupLabel: string; items: Category[] }[] = [];
  for (const category of categories) {
    let group = groups.find((g) => g.groupLabel === category.group_label);
    if (!group) {
      group = { groupLabel: category.group_label, items: [] };
      groups.push(group);
    }
    group.items.push(category);
  }

  return (
    <select
      value={value ?? ''}
      onChange={(e) => onChange(Number(e.target.value) || null)}
      disabled={loading || categories.length === 0}
      style={{
        padding: '6px 8px',
        fontSize: '13px',
        border: '1px solid #e5e5e5',
        borderRadius: '4px',
        backgroundColor: '#ffffff',
        color: '#111827',
      }}
    >
      <option value="" disabled>
        {loading ? 'Chargement...' : 'Sélectionner une catégorie'}
      </option>
      {groups.map((group) => (
        <optgroup key={group.groupLabel} label={group.groupLabel}>
          {group.items.map((category) => (
            <option key={category.id} value={category.id}>
              {category.label}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  );
}
