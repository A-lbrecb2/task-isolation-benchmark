import { Component, OnInit } from '@angular/core';
declare var $: any;
@Component({
  selector: 'app-notifications',
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.css']
})
export class NotificationsComponent implements OnInit {

  lastNotification: { from: string; align: string; type: string; message: string } | null = null;

  constructor() { }

  pickType(index: number): string {
      switch (index) {
          case 1: return 'info';
          case 2: return 'success';
          case 3: return 'warning';
          case 4: return 'danger';
          default: return 'info';
      }
  }

  showNotification(from: string, align: string, message?: string): void {
      const resolvedMessage = message === undefined
          ? "Welcome to <b>Material Dashboard</b> - a beautiful freebie for every web developer."
          : message;

      const color = Math.floor((Math.random() * 4) + 1);
      const type = this.pickType(color);

      this.lastNotification = { from, align, type, message: resolvedMessage };

      $.notify({
          icon: "notifications",
          message: resolvedMessage

      },{
          type: type,
          timer: 4000,
          placement: {
              from: from,
              align: align
          },
          template: '<div data-notify="container" class="col-xl-4 col-lg-4 col-11 col-sm-4 col-md-4 alert alert-{0} alert-with-icon" role="alert">' +
            '<button mat-button  type="button" aria-hidden="true" class="close mat-button" data-notify="dismiss">  <i class="material-icons">close</i></button>' +
            '<i class="material-icons" data-notify="icon">notifications</i> ' +
            '<span data-notify="title">{1}</span> ' +
            '<span data-notify="message">{2}</span>' +
            '<div class="progress" data-notify="progressbar">' +
              '<div class="progress-bar progress-bar-{0}" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;"></div>' +
            '</div>' +
            '<a href="{3}" target="{4}" data-notify="url"></a>' +
          '</div>'
      });
  }
  ngOnInit() {
  }

}
