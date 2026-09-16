// Task-isolation benchmark T3: hidden acceptance tests. Copy to src/app/components/footer/ AFTER the agent has finished.
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FooterComponent } from './footer.component';

describe('T3 FooterComponent (benchmark)', () => {
  let fixture: ComponentFixture<FooterComponent>;
  let component: any;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ declarations: [FooterComponent] }).compileComponents();
    fixture = TestBed.createComponent(FooterComponent);
    component = fixture.componentInstance;
  });

  it('T3.1 has the documented defaults', () => {
    expect(component.companyName).toBe('Creative Tim');
    expect(component.companyUrl).toBe('https://www.creative-tim.com');
  });

  it('T3.2 copyrightYear follows the test date', () => {
    expect(component.copyrightYear).toBe(new Date().getFullYear());
    component.test = new Date(2031, 0, 1);
    expect(component.copyrightYear).toBe(2031);
  });

  it('T3.3 template uses the inputs', () => {
    component.companyName = 'Example Corp';
    component.companyUrl = 'https://www.example.com';
    component.test = new Date(2030, 5, 1);
    fixture.detectChanges();
    const copyright: HTMLElement = fixture.nativeElement.querySelector('.copyright');
    expect(copyright.textContent).toContain('2030');
    expect(copyright.textContent).toContain('Example Corp');
    const link: HTMLAnchorElement = copyright.querySelector('a');
    expect(link.getAttribute('href')).toBe('https://www.example.com');
  });
});
