import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent {
  formData = {
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    company_name: '',
    nature_of_business: '',
    website: '',
    address: ''
  };
  loading = false;
  error = '';
  success = false;

  constructor(private authService: AuthService) {}

  register(): void {
    this.loading = true;
    this.authService.register(this.formData).subscribe({
      next: () => {
        this.success = true;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Registration failed';
        this.loading = false;
      }
    });
  }
}
