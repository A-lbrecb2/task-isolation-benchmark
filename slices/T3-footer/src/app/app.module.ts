import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { AppComponent } from './app.component';
import { FooterComponent } from './components/footer/footer.component';

@NgModule({
  imports: [BrowserModule, CommonModule],
  declarations: [AppComponent, FooterComponent],
  bootstrap: [AppComponent]
})
export class AppModule { }
