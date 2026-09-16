// Task-isolation benchmark T2: hidden acceptance tests. Copy to src/app/components/sidebar/ AFTER the agent has finished.
import { SidebarComponent, ROUTES } from './sidebar.component';

describe('T2 SidebarComponent (benchmark)', () => {
  let component: any;

  beforeEach(() => {
    component = new SidebarComponent();
    component.ngOnInit();
  });

  it('T2.1 ROUTES is unchanged', () => {
    expect(ROUTES.length).toBe(8);
    expect(ROUTES.map(r => r.path)).toEqual([
      '/dashboard', '/user-profile', '/table-list', '/typography',
      '/icons', '/maps', '/notifications', '/upgrade',
    ]);
  });

  it('T2.2 filterMenu matches titles case-insensitively', () => {
    component.filterMenu('table');
    expect(component.menuItems.length).toBe(1);
    expect(component.menuItems[0].path).toBe('/table-list');
    component.filterMenu('PRO');
    expect(component.menuItems.map((m: any) => m.path)).toEqual(['/user-profile', '/upgrade']);
  });

  it('T2.3 empty or whitespace query restores the full list', () => {
    component.filterMenu('maps');
    expect(component.menuItems.length).toBe(1);
    component.filterMenu('');
    expect(component.menuItems.length).toBe(8);
    component.filterMenu('   ');
    expect(component.menuItems.length).toBe(8);
  });

  it('T2.4 activeFilter holds the trimmed last query', () => {
    component.filterMenu('  Icons ');
    expect(component.activeFilter).toBe('Icons');
    expect(component.menuItems.length).toBe(1);
    component.filterMenu('');
    expect(component.activeFilter).toBe('');
  });
});
