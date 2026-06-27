import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CadService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  generateFromPrompt(prompt: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/cad/generate-from-prompt`, { prompt });
  }

  generateFromImage(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/cad/generate-from-image`, formData);
  }

  generateFromSketch(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/cad/generate-from-sketch`, formData);
  }

  uploadBaseModel(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/cad/upload-base-model`, formData);
  }

  getJobStatus(jobId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/cad/job/${jobId}`);
  }
}
