// Task-isolation benchmark T4: hidden acceptance tests. Copy to src/app/notifications/ AFTER the agent has finished.
import { NotificationsComponent } from './notifications.component';

describe('T4 NotificationsComponent (benchmark)', () => {
  let component: any;
  let notifySpy: jasmine.Spy;
  let originalJQuery: any;

  beforeEach(() => {
    notifySpy = jasmine.createSpy('notify');
    originalJQuery = (window as any).$;
    (window as any).$ = { notify: notifySpy };
    component = new NotificationsComponent();
  });

  afterEach(() => {
    (window as any).$ = originalJQuery;
  });

  it('T4.1 pickType maps indices to bootstrap-notify types', () => {
    expect(component.pickType(1)).toBe('info');
    expect(component.pickType(2)).toBe('success');
    expect(component.pickType(3)).toBe('warning');
    expect(component.pickType(4)).toBe('danger');
    expect(component.pickType(0)).toBe('info');
    expect(component.pickType(9)).toBe('info');
  });

  it('T4.2 lastNotification starts as null and records every call', () => {
    expect(component.lastNotification).toBeNull();
    component.showNotification('top', 'right', 'Hello benchmark');
    expect(component.lastNotification.from).toBe('top');
    expect(component.lastNotification.align).toBe('right');
    expect(component.lastNotification.message).toBe('Hello benchmark');
    expect(['info', 'success', 'warning', 'danger']).toContain(component.lastNotification.type);
  });

  it('T4.3 custom message reaches $.notify', () => {
    component.showNotification('bottom', 'left', 'Hello benchmark');
    expect(notifySpy).toHaveBeenCalledTimes(1);
    const [content, options] = notifySpy.calls.mostRecent().args;
    expect(content.message).toBe('Hello benchmark');
    expect(options.placement).toEqual({ from: 'bottom', align: 'left' });
    expect(options.type).toBe(component.lastNotification.type);
  });

  it('T4.4 default message is kept when message is omitted', () => {
    component.showNotification('top', 'center');
    const [content] = notifySpy.calls.mostRecent().args;
    expect(content.message).toContain('Material Dashboard');
    expect(component.lastNotification.message).toBe(content.message);
  });
});
