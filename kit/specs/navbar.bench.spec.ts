// Task-isolation benchmark T6: hidden acceptance tests. Copy to src/app/components/navbar/ AFTER the agent has finished.
import { NavbarComponent } from './navbar.component';
import { ROUTES } from '../sidebar/sidebar.component';

function make(path: string): any {
  const location = { path: () => path, prepareExternalUrl: (p: string) => p } as any;
  const element = { nativeElement: document.createElement('nav') } as any;
  const router = { events: { subscribe: () => ({ unsubscribe() {} }) } } as any;
  return new NavbarComponent(location, element, router);
}

describe('T6 NavbarComponent (benchmark)', () => {
  it('T6.1 resolveTitle normalises the path and falls back to Dashboard', () => {
    const c = make('/');
    expect(c.resolveTitle('/table-list')).toBe('Table List');
    expect(c.resolveTitle('/table-list?tab=2')).toBe('Table List');
    expect(c.resolveTitle('#/icons')).toBe('Icons');
    expect(c.resolveTitle('/maps/')).toBe('Maps');
    expect(c.resolveTitle('/user-profile#top')).toBe('User Profile');
    expect(c.resolveTitle('/does-not-exist')).toBe('Dashboard');
    expect(c.resolveTitle('/')).toBe('Dashboard');
  });

  it('T6.2 getTitle uses the current location, query string included', () => {
    expect(make('/table-list?tab=2').getTitle()).toBe('Table List');
    expect(make('/notifications').getTitle()).toBe('Notifications');
    expect(make('/nowhere').getTitle()).toBe('Dashboard');
  });

  it('T6.3 brandTitle and breadcrumb', () => {
    const c = make('/typography');
    expect(c.brandTitle).toBe('Material Dashboard');
    expect(c.breadcrumb).toBe('Material Dashboard › Typography');
    c.brandTitle = 'Acme';
    expect(c.breadcrumb).toBe('Acme › Typography');
  });

  it('T6.4 sidebarVisible is public and ROUTES is untouched', () => {
    const c = make('/');
    expect(typeof c.sidebarVisible).toBe('boolean');
    expect(c.sidebarVisible).toBeFalse();
    expect(ROUTES.length).toBe(8);
    expect(ROUTES.map(r => r.path)).toEqual([
      '/dashboard', '/user-profile', '/table-list', '/typography',
      '/icons', '/maps', '/notifications', '/upgrade',
    ]);
  });
});
