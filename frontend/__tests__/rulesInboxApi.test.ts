import { rulesAPI, inboxAPI, categoriesAPI } from '@/api/client';

beforeEach(() => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true, status: 200, json: async () => ({ items: [] }),
  }) as unknown as typeof fetch;
});

test('rulesAPI.list appelle /api/rules avec property_id', async () => {
  await rulesAPI.list(25);
  expect(global.fetch).toHaveBeenCalledWith(
    expect.stringContaining('/api/rules?property_id=25'), expect.anything());
});

test('inboxAPI.validate poste sur /api/inbox/validate', async () => {
  await inboxAPI.validate({ transaction_id: 1, category_id: 2 });
  // fetchAPI émet aussi un log applicatif via fetch('/api/logs/frontend') avant la requête
  // réelle : on retrouve l'appel voulu par URL plutôt que de supposer qu'il est le premier.
  const call = (global.fetch as jest.Mock).mock.calls.find(([url]: [string]) =>
    url.includes('/api/inbox/validate'));
  expect(call).toBeDefined();
  const [url, opts] = call as [string, RequestInit];
  expect(url).toContain('/api/inbox/validate');
  expect(opts.method).toBe('POST');
});

test('categoriesAPI.list appelle /api/categories', async () => {
  await categoriesAPI.list();
  expect(global.fetch).toHaveBeenCalledWith(
    expect.stringContaining('/api/categories'), expect.anything());
});
