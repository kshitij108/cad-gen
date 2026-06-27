"""
Batch Processing System
Generate multiple CAD models in parallel or sequential mode
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import asyncio


class BatchProcessingMode(str, Enum):
    """Batch processing modes"""
    SEQUENTIAL = "sequential"      # One at a time
    PARALLEL = "parallel"          # All at once
    THROTTLED = "throttled"        # Limited concurrency


class BatchJobStatus(str, Enum):
    """Batch job statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial_failure"
    FAILED = "failed"


class BatchRequest:
    """Represents a batch of generation requests"""
    
    def __init__(
        self,
        batch_id: str,
        requests: List[Dict],
        mode: BatchProcessingMode = BatchProcessingMode.SEQUENTIAL,
        max_concurrent: int = 3,
        user_id: Optional[str] = None
    ):
        self.batch_id = batch_id
        self.requests = requests
        self.mode = mode
        self.max_concurrent = max_concurrent
        self.user_id = user_id
        self.created_at = datetime.utcnow().isoformat()
        self.started_at = None
        self.completed_at = None
        self.status = BatchJobStatus.PENDING
        self.job_ids = []
        self.results = {}


class BatchProcessor:
    """Processes multiple CAD generation requests"""
    
    def __init__(self, pipeline, output_dir: Path = Path("./cad_models")):
        self.pipeline = pipeline
        self.output_dir = output_dir
        self.batches = {}
    
    async def create_batch(
        self,
        requests: List[Dict],
        mode: BatchProcessingMode = BatchProcessingMode.SEQUENTIAL,
        max_concurrent: int = 3,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Create a new batch job
        
        Args:
            requests: List of generation requests (can be prompts or image paths)
            mode: Processing mode (sequential, parallel, throttled)
            max_concurrent: Max concurrent jobs for throttled mode
            user_id: Optional user ID
            
        Returns:
            Batch information with batch_id
        """
        if not requests or len(requests) == 0:
            return {
                "status": "error",
                "error": "No requests provided"
            }
        
        batch_id = str(uuid.uuid4())
        batch = BatchRequest(
            batch_id,
            requests,
            mode,
            max_concurrent,
            user_id
        )
        
        self.batches[batch_id] = batch
        
        return {
            "status": "created",
            "batch_id": batch_id,
            "total_requests": len(requests),
            "mode": mode,
            "estimated_time": self._estimate_time(len(requests), mode)
        }
    
    async def process_batch(self, batch_id: str) -> Dict:
        """
        Start processing a batch
        
        Args:
            batch_id: ID of batch to process
            
        Returns:
            Batch status with job IDs
        """
        if batch_id not in self.batches:
            return {
                "status": "error",
                "error": "Batch not found"
            }
        
        batch = self.batches[batch_id]
        batch.status = BatchJobStatus.PROCESSING
        batch.started_at = datetime.utcnow().isoformat()
        
        try:
            if batch.mode == BatchProcessingMode.SEQUENTIAL:
                await self._process_sequential(batch)
            elif batch.mode == BatchProcessingMode.PARALLEL:
                await self._process_parallel(batch)
            else:  # throttled
                await self._process_throttled(batch)
            
            batch.completed_at = datetime.utcnow().isoformat()
            batch.status = BatchJobStatus.COMPLETED
            
        except Exception as e:
            batch.status = BatchJobStatus.FAILED
            batch.completed_at = datetime.utcnow().isoformat()
            return {
                "status": "error",
                "error": str(e),
                "partial_results": batch.results
            }
        
        return {
            "status": "completed",
            "batch_id": batch_id,
            "job_ids": batch.job_ids,
            "results": batch.results,
            "summary": self._generate_summary(batch)
        }
    
    async def _process_sequential(self, batch: BatchRequest):
        """Process requests one at a time"""
        for i, request in enumerate(batch.requests):
            job_id = await self._process_single_request(request)
            if job_id:
                batch.job_ids.append(job_id)
                batch.results[job_id] = {
                    "sequence": i + 1,
                    "status": "completed"
                }
    
    async def _process_parallel(self, batch: BatchRequest):
        """Process all requests concurrently"""
        tasks = [
            self._process_single_request(req)
            for req in batch.requests
        ]
        
        job_ids = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, job_id in enumerate(job_ids):
            if isinstance(job_id, str):
                batch.job_ids.append(job_id)
                batch.results[job_id] = {"sequence": i + 1, "status": "completed"}
            else:
                batch.results[f"error_{i}"] = {"error": str(job_id)}
    
    async def _process_throttled(self, batch: BatchRequest):
        """Process with limited concurrency"""
        semaphore = asyncio.Semaphore(batch.max_concurrent)
        
        async def limited_process(request):
            async with semaphore:
                return await self._process_single_request(request)
        
        tasks = [
            limited_process(req)
            for req in batch.requests
        ]
        
        job_ids = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, job_id in enumerate(job_ids):
            if isinstance(job_id, str):
                batch.job_ids.append(job_id)
                batch.results[job_id] = {"sequence": i + 1, "status": "completed"}
            else:
                batch.results[f"error_{i}"] = {"error": str(job_id)}
    
    async def _process_single_request(self, request: Dict) -> Optional[str]:
        """Process a single generation request"""
        try:
            job_id = str(uuid.uuid4())
            
            if "prompt" in request:
                result = await self.pipeline.generate_from_prompt(
                    request["prompt"],
                    job_id
                )
            elif "image_path" in request:
                result = await self.pipeline.generate_from_image(
                    request["image_path"],
                    job_id
                )
            else:
                return None
            
            return job_id if result.get("status") == "success" else None
        
        except Exception as e:
            print(f"Error processing request: {e}")
            return None
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """Get current status of a batch"""
        if batch_id not in self.batches:
            return {
                "status": "error",
                "error": "Batch not found"
            }
        
        batch = self.batches[batch_id]
        
        return {
            "batch_id": batch_id,
            "status": batch.status,
            "total_requests": len(batch.requests),
            "completed_jobs": len(batch.job_ids),
            "job_ids": batch.job_ids,
            "results_summary": self._generate_summary(batch),
            "created_at": batch.created_at,
            "started_at": batch.started_at,
            "completed_at": batch.completed_at
        }
    
    def get_batch_results(self, batch_id: str, details: bool = False) -> Dict:
        """Get detailed results of a batch"""
        if batch_id not in self.batches:
            return {
                "status": "error",
                "error": "Batch not found"
            }
        
        batch = self.batches[batch_id]
        
        results = {
            "batch_id": batch_id,
            "status": batch.status,
            "total_jobs": len(batch.job_ids),
            "jobs": []
        }
        
        if details:
            for job_id in batch.job_ids:
                job_details = {
                    "job_id": job_id,
                    "result": batch.results.get(job_id)
                }
                results["jobs"].append(job_details)
        else:
            results["jobs"] = batch.job_ids
        
        return results
    
    def export_batch_manifest(self, batch_id: str, format: str = "json") -> Dict:
        """
        Export batch manifest for tracking
        
        Args:
            batch_id: Batch ID
            format: Export format (json, csv)
            
        Returns:
            Manifest data
        """
        if batch_id not in self.batches:
            return {"error": "Batch not found"}
        
        batch = self.batches[batch_id]
        
        manifest = {
            "batch_id": batch_id,
            "created_at": batch.created_at,
            "completed_at": batch.completed_at,
            "status": batch.status,
            "mode": batch.mode,
            "requests": []
        }
        
        for i, request in enumerate(batch.requests):
            job_id = batch.job_ids[i] if i < len(batch.job_ids) else None
            
            manifest["requests"].append({
                "index": i + 1,
                "type": "prompt" if "prompt" in request else "image",
                "content": request.get("prompt", request.get("image_path", "")),
                "job_id": job_id,
                "result": batch.results.get(job_id) if job_id else None
            })
        
        return manifest
    
    def _estimate_time(self, num_requests: int, mode: BatchProcessingMode) -> str:
        """Estimate processing time based on mode"""
        # Rough estimates: 10-40s per model
        avg_time_per_model = 25
        
        if mode == BatchProcessingMode.SEQUENTIAL:
            total_seconds = num_requests * avg_time_per_model
        elif mode == BatchProcessingMode.PARALLEL:
            total_seconds = avg_time_per_model * 1.5  # Overhead
        else:  # throttled
            total_seconds = (num_requests / 3) * avg_time_per_model
        
        minutes = int(total_seconds / 60)
        seconds = int(total_seconds % 60)
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    
    def _generate_summary(self, batch: BatchRequest) -> Dict:
        """Generate summary statistics for a batch"""
        successful = len(batch.job_ids)
        failed = len(batch.requests) - successful
        
        # Calculate average quality
        total_quality = 0
        quality_count = 0
        
        for job_id in batch.job_ids:
            job_dir = self.output_dir / job_id
            val_file = job_dir / "stl_validation.json"
            
            if val_file.exists():
                try:
                    with open(val_file) as f:
                        data = json.load(f)
                        total_quality += data.get("quality_score", 0)
                        quality_count += 1
                except:
                    pass
        
        avg_quality = (total_quality / quality_count) if quality_count > 0 else 0
        
        return {
            "total_requests": len(batch.requests),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/len(batch.requests)*100):.1f}%",
            "average_quality_score": f"{avg_quality:.1f}/100"
        }


def get_batch_processor(pipeline) -> BatchProcessor:
    """Get batch processor instance"""
    return BatchProcessor(pipeline)
