import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { AppComponent } from './app.component';
import { NotificationsComponent } from './notifications/notifications.component';

@NgModule({
  imports: [BrowserModule, CommonModule],
  declarations: [AppComponent, NotificationsComponent],
  bootstrap: [AppComponent]
})
export class AppModule { }
