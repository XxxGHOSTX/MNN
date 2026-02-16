"""
Checkpoint Module for MNN Pipeline

Provides checkpoint persistence and replay capabilities for the MNN pipeline.
Checkpoints store intermediate results (constraints, indices, sequences) and
final outputs for deterministic verification and debugging.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class CheckpointManager:
    """
    Manages checkpoint persistence and replay for MNN pipeline.
    
    Checkpoints are stored as JSON files with deterministic filenames based
    on event IDs, allowing for reliable replay and verification.
    """
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory for storing checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(
        self,
        event_id: str,
        query: str,
        normalized_query: str,
        constraints: Any,
        indices: Any,
        sequences: Any,
        results: List[Dict[str, Any]],
        timings: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Save a complete pipeline checkpoint.
        
        Args:
            event_id: Deterministic event ID
            query: Original query
            normalized_query: Normalized query
            constraints: Generated constraints
            indices: Mapped indices
            sequences: Generated sequences
            results: Final ranked results
            timings: Optional stage timings
            
        Returns:
            Path to saved checkpoint file
        """
        checkpoint_data = {
            "event_id": event_id,
            "query": query,
            "normalized_query": normalized_query,
            "constraints": self._serialize_data(constraints),
            "indices": self._serialize_data(indices),
            "sequences": self._serialize_data(sequences),
            "results": results,
            "timings": timings or {},
        }
        
        # Use event_id as filename for determinism
        checkpoint_file = self.checkpoint_dir / f"{event_id}.json"
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        return str(checkpoint_file)
    
    def load_checkpoint(self, event_id: str) -> Dict[str, Any]:
        """
        Load a checkpoint by event ID.
        
        Args:
            event_id: Event ID of checkpoint to load
            
        Returns:
            Checkpoint data dictionary
            
        Raises:
            FileNotFoundError: If checkpoint doesn't exist
        """
        checkpoint_file = self.checkpoint_dir / f"{event_id}.json"
        
        if not checkpoint_file.exists():
            raise FileNotFoundError(f"Checkpoint not found: {event_id}")
        
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    
    def list_checkpoints(self) -> List[str]:
        """
        List all available checkpoint event IDs.
        
        Returns:
            List of event IDs (sorted)
        """
        checkpoints = []
        for file in self.checkpoint_dir.glob("*.json"):
            event_id = file.stem
            checkpoints.append(event_id)
        
        return sorted(checkpoints)
    
    def delete_checkpoint(self, event_id: str) -> bool:
        """
        Delete a checkpoint by event ID.
        
        Args:
            event_id: Event ID of checkpoint to delete
            
        Returns:
            True if deleted, False if not found
        """
        checkpoint_file = self.checkpoint_dir / f"{event_id}.json"
        
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            return True
        
        return False
    
    def _serialize_data(self, data: Any) -> Any:
        """
        Serialize data for JSON storage.
        
        Handles various data types that might not be JSON-serializable.
        """
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, (list, tuple)):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        else:
            # Convert other types to string representation
            return str(data)


def replay_checkpoint(
    checkpoint_manager: CheckpointManager,
    event_id: str
) -> Dict[str, Any]:
    """
    Replay a checkpoint and return its results.
    
    This is useful for verification and debugging. The replay simply
    loads the checkpoint and returns the stored results without
    re-executing the pipeline (use for verification that checkpoints
    match live execution).
    
    Args:
        checkpoint_manager: CheckpointManager instance
        event_id: Event ID to replay
        
    Returns:
        Dictionary with checkpoint data and results
    """
    checkpoint = checkpoint_manager.load_checkpoint(event_id)
    
    return {
        "event_id": checkpoint["event_id"],
        "query": checkpoint["query"],
        "normalized_query": checkpoint["normalized_query"],
        "results": checkpoint["results"],
        "timings": checkpoint.get("timings", {}),
        "checkpoint_file": f"{event_id}.json",
    }
