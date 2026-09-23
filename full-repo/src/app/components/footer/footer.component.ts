import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.css']
})
export class FooterComponent implements OnInit {
  test : Date = new Date();

  @Input() companyName: string = 'Creative Tim';
  @Input() companyUrl: string = 'https://www.creative-tim.com';

  constructor() { }

  ngOnInit() {
  }

  get copyrightYear(): number {
    return this.test.getFullYear();
  }

}
