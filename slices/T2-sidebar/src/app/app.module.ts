import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AppComponent } from './app.component';
import { SidebarComponent } from './components/sidebar/sidebar.component';

@NgModule({
  imports: [BrowserModule, CommonModule, RouterModule.forRoot([])],
  declarations: [AppComponent, SidebarComponent],
  bootstrap: [AppComponent]
})
export class AppModule { }
