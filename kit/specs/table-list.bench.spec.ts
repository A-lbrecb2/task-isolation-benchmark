// Task-isolation benchmark T1: hidden acceptance tests. Copy to src/app/table-list/ AFTER the agent has finished.
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { TableListComponent } from './table-list.component';

describe('T1 TableListComponent (benchmark)', () => {
  let fixture: ComponentFixture<TableListComponent>;
  let component: any;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [TableListComponent],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
    fixture = TestBed.createComponent(TableListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('T1.1 exposes six employees', () => {
    expect(Array.isArray(component.employees)).toBeTrue();
    expect(component.employees.length).toBe(6);
  });

  it('T1.2 keeps the original rows with numeric salaries', () => {
    const byId = (id: number) => component.employees.find((e: any) => e.id === id);
    expect(byId(1).name).toBe('Dakota Rice');
    expect(byId(1).country).toBe('Niger');
    expect(byId(1).city).toBe('Oud-Turnhout');
    expect(byId(1).salary).toBe(36738);
    expect(byId(5).city).toBe('Feldkirchen in Kärnten');
    expect(byId(6).salary).toBe(78615);
    component.employees.forEach((e: any) => expect(typeof e.salary).toBe('number'));
  });

  it('T1.3 totalSalary() sums all salaries', () => {
    expect(component.totalSalary()).toBe(297561);
  });

  it('T1.4 template renders the rows from the array', () => {
    const rows = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(rows.length).toBe(12);
    const html: string = fixture.nativeElement.innerHTML;
    expect(html).toContain('Dakota Rice');
    expect(html).toContain('$36,738');
  });
});
