#!/usr/bin/env python3
"""
Checkpoint Replay Utility

Replays saved checkpoints to verify deterministic behavior and debug issues.
Can be used to replay individual checkpoints or compare multiple runs.
"""

import argparse
import json
import sys
from pathlib import Path

from checkpoints import CheckpointManager, replay_checkpoint


def list_checkpoints(checkpoint_dir: str) -> None:
    """List all available checkpoints."""
    manager = CheckpointManager(checkpoint_dir)
    checkpoints = manager.list_checkpoints()
    
    if not checkpoints:
        print(f"No checkpoints found in {checkpoint_dir}")
        return
    
    print(f"Found {len(checkpoints)} checkpoints:\n")
    for event_id in checkpoints:
        try:
            checkpoint = manager.load_checkpoint(event_id)
            query = checkpoint.get("query", "unknown")
            result_count = len(checkpoint.get("results", []))
            print(f"  {event_id}")
            print(f"    Query: {query[:50]}{'...' if len(query) > 50 else ''}")
            print(f"    Results: {result_count}")
            print()
        except Exception as e:
            print(f"  {event_id} (error loading: {e})")


def replay_one(event_id: str, checkpoint_dir: str, verbose: bool = False) -> None:
    """Replay a single checkpoint."""
    manager = CheckpointManager(checkpoint_dir)
    
    try:
        result = replay_checkpoint(manager, event_id)
        
        print(f"Replayed checkpoint: {event_id}")
        print(f"Query: {result['query']}")
        print(f"Normalized: {result['normalized_query']}")
        print(f"Results: {len(result['results'])}")
        print(f"Checkpoint file: {result['checkpoint_file']}")
        
        if result['timings']:
            print("\nTimings:")
            for stage, duration in sorted(result['timings'].items()):
                print(f"  {stage}: {duration:.2f}ms")
        
        if verbose:
            print("\nResults:")
            for i, res in enumerate(result['results'], 1):
                print(f"\n{i}. Score: {res.get('score', 0):.4f}")
                seq = res.get('sequence', '')
                print(f"   {seq[:100]}{'...' if len(seq) > 100 else ''}")
    
    except FileNotFoundError:
        print(f"Error: Checkpoint not found: {event_id}")
        sys.exit(1)
    except Exception as e:
        print(f"Error replaying checkpoint: {e}")
        sys.exit(1)


def export_checkpoint(event_id: str, checkpoint_dir: str, output_file: str) -> None:
    """Export checkpoint to a formatted JSON file."""
    manager = CheckpointManager(checkpoint_dir)
    
    try:
        checkpoint = manager.load_checkpoint(event_id)
        
        with open(output_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"Exported checkpoint {event_id} to {output_file}")
    
    except FileNotFoundError:
        print(f"Error: Checkpoint not found: {event_id}")
        sys.exit(1)
    except Exception as e:
        print(f"Error exporting checkpoint: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Replay and manage MNN pipeline checkpoints"
    )
    
    parser.add_argument(
        '--checkpoint-dir',
        default='checkpoints',
        help='Checkpoint directory (default: checkpoints)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    subparsers.add_parser('list', help='List all checkpoints')
    
    # Replay command
    replay_parser = subparsers.add_parser('replay', help='Replay a checkpoint')
    replay_parser.add_argument('event_id', help='Event ID to replay')
    replay_parser.add_argument('-v', '--verbose', action='store_true',
                              help='Show detailed results')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export checkpoint to file')
    export_parser.add_argument('event_id', help='Event ID to export')
    export_parser.add_argument('-o', '--output', required=True,
                              help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'list':
        list_checkpoints(args.checkpoint_dir)
    elif args.command == 'replay':
        replay_one(args.event_id, args.checkpoint_dir, args.verbose)
    elif args.command == 'export':
        export_checkpoint(args.event_id, args.checkpoint_dir, args.output)


if __name__ == '__main__':
    main()
