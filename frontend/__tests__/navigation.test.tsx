import { render, screen } from '@testing-library/react';
import Navigation from '@/components/Navigation';

jest.mock('next/navigation', () => ({
  usePathname: () => '/dashboard/transactions',
  useSearchParams: () => new URLSearchParams('tab=rules'),
}));

test('les onglets Boîte de réception et Règles sont présents', () => {
  render(<Navigation />);
  expect(screen.getByText('Boîte de réception')).toBeInTheDocument();
  expect(screen.getByText('Règles')).toBeInTheDocument();
});
