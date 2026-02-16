#!/usr/bin/env python3
"""
Metrics Export Utility

Exports current metrics to JSON or human-readable format for analysis.
"""

import argparse
import json
import sys
from datetime import datetime

from metrics import get_metrics_snapshot


def export_json(output_file: str = None) -> None:
    """Export metrics as JSON."""
    snapshot = get_metrics_snapshot()
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
        print(f"Metrics exported to {output_file}")
    else:
        print(json.dumps(snapshot, indent=2))


def export_human_readable(output_file: str = None) -> None:
    """Export metrics in human-readable format."""
    snapshot = get_metrics_snapshot()
    
    lines = []
    lines.append("=" * 60)
    lines.append("MNN Pipeline Metrics Snapshot")
    lines.append("=" * 60)
    lines.append("")
    
    # Timestamp
    timestamp = datetime.fromtimestamp(snapshot["timestamp"])
    lines.append(f"Captured: {timestamp.isoformat()}")
    lines.append("")
    
    # Counters
    lines.append("Counters:")
    lines.append("-" * 60)
    if snapshot["counters"]:
        for name, value in sorted(snapshot["counters"].items()):
            lines.append(f"  {name:40s} {value:10d}")
    else:
        lines.append("  (no counters)")
    lines.append("")
    
    # Timings
    lines.append("Timings (ms):")
    lines.append("-" * 60)
    if snapshot["timings"]:
        for name, stats in sorted(snapshot["timings"].items()):
            lines.append(f"  {name}:")
            lines.append(f"    Count:    {stats['count']:8d}")
            lines.append(f"    Min:      {stats['min']:8.2f}")
            lines.append(f"    Max:      {stats['max']:8.2f}")
            lines.append(f"    Avg:      {stats['avg']:8.2f}")
            lines.append(f"    P50:      {stats['p50']:8.2f}")
            lines.append(f"    P95:      {stats['p95']:8.2f}")
            lines.append(f"    P99:      {stats['p99']:8.2f}")
            lines.append("")
    else:
        lines.append("  (no timing data)")
        lines.append("")
    
    # Cache stats
    lines.append("Cache Statistics:")
    lines.append("-" * 60)
    if snapshot["cache_stats"]:
        for cache_name, stats in sorted(snapshot["cache_stats"].items()):
            total = stats["hits"] + stats["misses"]
            hit_rate = (stats["hits"] / total * 100) if total > 0 else 0
            lines.append(f"  {cache_name}:")
            lines.append(f"    Hits:     {stats['hits']:8d}")
            lines.append(f"    Misses:   {stats['misses']:8d}")
            lines.append(f"    Hit Rate: {hit_rate:7.1f}%")
            lines.append(f"    Size:     {stats['size']:8d} / {stats['maxsize']:d}")
            lines.append("")
    else:
        lines.append("  (no cache data)")
        lines.append("")
    
    # Recent requests
    lines.append(f"Recent Requests (last {len(snapshot['recent_requests'])}):")
    lines.append("-" * 60)
    if snapshot["recent_requests"]:
        for req in snapshot["recent_requests"]:
            event_id = req.get("event_id", "unknown")[:20]
            lines.append(f"  Event: {event_id}...")
            lines.append(f"    Query length:      {req.get('query_length', 0)}")
            lines.append(f"    Results:           {req.get('result_count', 0)}")
            lines.append(f"    Total time:        {req.get('total_ms', 0):.2f}ms")
            lines.append("")
    else:
        lines.append("  (no recent requests)")
    
    lines.append("=" * 60)
    
    output = "\n".join(lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Metrics exported to {output_file}")
    else:
        print(output)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Export MNN pipeline metrics"
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file (default: stdout)'
    )
    
    args = parser.parse_args()
    
    if args.format == 'json':
        export_json(args.output)
    else:
        export_human_readable(args.output)


if __name__ == '__main__':
    main()
