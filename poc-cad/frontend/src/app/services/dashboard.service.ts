import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getProjects(): Observable<any> {
    return this.http.get(`${this.apiUrl}/projects`);
  }

  getSpaces(): Observable<any> {
    return this.http.get(`${this.apiUrl}/spaces`);
  }

  getCatalogs(): Observable<any> {
    return this.http.get(`${this.apiUrl}/catalogs`);
  }

  getJobs(): Observable<any> {
    return this.http.get(`${this.apiUrl}/jobs`);
  }

  getUserProfile(): Observable<any> {
    return this.http.get(`${this.apiUrl}/user/profile`);
  }
}
