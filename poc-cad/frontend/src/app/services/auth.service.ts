import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, userData);
  }

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/login`, { email, password });
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/forgot-password`, { email });
  }

  saveToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  saveUserInfo(userInfo: any): void {
    localStorage.setItem('user_email', userInfo.email);
    localStorage.setItem('user_name', `${userInfo.first_name} ${userInfo.last_name}`);
  }

  getUserEmail(): string | null {
    return localStorage.getItem('user_email');
  }

  getUserName(): string | null {
    return localStorage.getItem('user_name');
  }

  logout(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_name');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}
