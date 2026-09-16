// Crodox benchmark T5: hidden acceptance tests. Copy to src/app/dashboard/ AFTER the agent has finished.
import { DashboardComponent } from './dashboard.component';

describe('T5 DashboardComponent (benchmark)', () => {
  let component: any;

  beforeEach(() => {
    component = new DashboardComponent();
  });

  it('T5.1 daily sales data matches the original values', () => {
    const d = component.getDailySalesData();
    expect(d.labels).toEqual(['M', 'T', 'W', 'T', 'F', 'S', 'S']);
    expect(d.series).toEqual([[12, 17, 7, 17, 23, 18, 38]]);
  });

  it('T5.2 completed tasks and website views data match the original values', () => {
    const c = component.getCompletedTasksData();
    expect(c.labels).toEqual(['12p', '3p', '6p', '9p', '12p', '3a', '6a', '9a']);
    expect(c.series).toEqual([[230, 750, 450, 300, 280, 240, 200, 190]]);
    const w = component.getWebsiteViewsData();
    expect(w.labels.length).toBe(12);
    expect(w.series).toEqual([[542, 443, 320, 780, 553, 453, 326, 434, 568, 610, 756, 895]]);
  });

  it('T5.3 suggestedHigh returns the next multiple of 10 above the maximum', () => {
    expect(component.suggestedHigh([[12, 17, 7, 17, 23, 18, 38]])).toBe(40);
    expect(component.suggestedHigh([[230, 750, 450]])).toBe(760);
    expect(component.suggestedHigh([[542, 895]])).toBe(900);
    expect(component.suggestedHigh([[10]])).toBe(20);
    expect(component.suggestedHigh([[1, 2], [3, 41]])).toBe(50);
  });
});
