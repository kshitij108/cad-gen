import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CadService } from '../../services/cad.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {
  inputMode: string = 'prompt';
  promptText: string = '';
  selectedFile: File | null = null;
  jobId: string | null = null;
  jobStatus: string = '';
  progress: number = 0;
  cadSpecification: string = '';
  fileUrl: string | null = null;
  loading: boolean = false;
  error: string = '';

  constructor(private cadService: CadService) {}

  onInputModeChange(mode: string): void {
    this.inputMode = mode;
    this.resetState();
  }

  onFileSelected(event: Event, mode: string): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.selectedFile = input.files[0];
      this.submitCADRequest(mode);
    }
  }

  submitCADRequest(mode: string): void {
    this.loading = true;
    this.error = '';
    
    if (mode === 'prompt' && this.promptText) {
      this.cadService.generateFromPrompt(this.promptText).subscribe({
        next: (response) => {
          this.handleResponse(response);
        },
        error: (err) => {
          this.loading = false;
          this.error = 'Failed to generate CAD: ' + (err.error?.error || 'Unknown error');
        }
      });
    } else if (this.selectedFile) {
      let service;
      if (mode === 'reference') {
        service = this.cadService.generateFromImage(this.selectedFile);
      } else if (mode === 'sketch') {
        service = this.cadService.generateFromSketch(this.selectedFile);
      } else if (mode === 'cad') {
        service = this.cadService.uploadBaseModel(this.selectedFile);
      }

      if (service) {
        service.subscribe({
          next: (response) => {
            this.handleResponse(response);
          },
          error: (err) => {
            this.loading = false;
            this.error = 'Failed to process file: ' + (err.error?.error || 'Unknown error');
          }
        });
      }
    }
  }

  private handleResponse(response: any): void {
    this.jobId = response.job_id;
    this.jobStatus = response.status;
    this.progress = response.progress || 0;
    this.cadSpecification = response.cad_specification || '';
    this.fileUrl = response.file_url || null;
    
    if (this.jobStatus === 'processing') {
      this.loading = true;
      this.checkJobStatus();
    } else if (this.jobStatus === 'completed') {
      this.loading = false;
    } else {
      this.loading = false;
      this.error = response.error || 'Generation failed';
    }
  }

  checkJobStatus(): void {
    if (!this.jobId) return;

    this.cadService.getJobStatus(this.jobId).subscribe({
      next: (response) => {
        this.jobStatus = response.status;
        this.progress = response.progress;
        this.cadSpecification = response.cad_specification || this.cadSpecification;
        this.fileUrl = response.file_url || null;

        if (this.jobStatus === 'processing') {
          setTimeout(() => this.checkJobStatus(), 1500);
        } else if (this.jobStatus === 'completed') {
          this.loading = false;
        } else {
          this.loading = false;
        }
      },
      error: (err) => {
        this.loading = false;
        console.error('Error checking job status:', err);
      }
    });
  }

  downloadCAD(): void {
    if (this.fileUrl) {
      window.open('http://localhost:8000' + this.fileUrl, '_blank');
    }
  }

  downloadSpecSheet(): void {
    if (this.cadSpecification) {
      try {
        const spec = JSON.parse(this.cadSpecification);
        const content = JSON.stringify(spec, null, 2);
        const blob = new Blob([content], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cad-spec-${this.jobId}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      } catch (e) {
        alert('Could not download specification');
      }
    }
  }

  private resetState(): void {
    this.jobId = null;
    this.jobStatus = '';
    this.progress = 0;
    this.cadSpecification = '';
    this.fileUrl = null;
    this.loading = false;
    this.error = '';
    this.selectedFile = null;
    this.promptText = '';
  }
}
