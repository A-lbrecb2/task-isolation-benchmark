import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { AppComponent } from './app.component';
import { TableListComponent } from './table-list/table-list.component';

@NgModule({
  imports: [BrowserModule, CommonModule],
  declarations: [AppComponent, TableListComponent],
  bootstrap: [AppComponent]
})
export class AppModule { }
