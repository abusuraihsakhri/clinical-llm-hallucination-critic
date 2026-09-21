"""Command-line interface for the deterministic critic workflow prototype."""
import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable

from agents.base import AuditLogger, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
REQUIRED_BATCH_COLUMNS = {"task_id", "target_identifier", "primary_metric"}
RESULT_COLUMNS = ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]


def _parse_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _batch_fieldnames(source: Iterable[str]) -> list[str]:
    fields = list(source)
    return fields + [name for name in RESULT_COLUMNS if name not in fields]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="clinical-llm-hallucination-critic",
        description="Deterministic rule-based prototype for exercising critic workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_audit = subparsers.add_parser("audit", help="Run one deterministic rule evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    p_chat = subparsers.add_parser("chat", help="Query the mock supervisory adapter")
    p_chat.add_argument("query", nargs="+")

    p_batch = subparsers.add_parser("batch", help="Process CSV records locally")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    subparsers.add_parser("verify-audit", help="Verify the current in-memory HMAC audit chain")

    p_serve = subparsers.add_parser("serve", help="Launch the optional FastAPI server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    try:
        if args.command == "audit":
            payload = SystemTaskPayload(
                task_id=args.task_id,
                target_identifier=args.target,
                primary_metric=args.primary,
                secondary_metric=args.secondary,
                status_descriptor=args.status,
                is_critical_flag=args.critical,
            )
            dossier = supervisor.process_task(payload)
            print(f"Task: {dossier.task_id}")
            print(f"Urgency: {dossier.overall_urgency.value}")
            print(f"Integrity state: {dossier.integrity_status.value}")
            print(f"Alerts: {dossier.total_alerts}")
            for alert in dossier.alerts:
                print(f"- {alert.origin_worker}: {alert.summary}")
            print(f"Audit hash: {dossier.audit_hash}")
            print("Note: prototype rules only; not a clinical hallucination detector or decision-support system.")
            return 0

        if args.command == "chat":
            print(supervisor.query_supervisory_chat(" ".join(args.query)))
            return 0

        if args.command == "verify-audit":
            print(f"Audit blocks: {len(AuditLogger.get_trail())} | HMAC chain valid: {AuditLogger.verify_integrity()}")
            return 0

        if args.command == "batch":
            input_path = Path(args.input)
            output_path = Path(args.output)
            if input_path.resolve() == output_path.resolve():
                parser.error("--output must be different from --input")

            with input_path.open(mode="r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = list(reader.fieldnames or [])
                missing = sorted(REQUIRED_BATCH_COLUMNS.difference(fieldnames))
                if missing:
                    parser.error(f"input CSV is missing required columns: {', '.join(missing)}")
                rows = list(reader)

            out_rows = []
            for row_number, row in enumerate(rows, start=2):
                try:
                    payload = SystemTaskPayload(
                        task_id=row.get("task_id") or f"TASK-{row_number}",
                        target_identifier=row.get("target_identifier") or "TARGET-01",
                        primary_metric=float(row["primary_metric"]),
                        secondary_metric=float(row.get("secondary_metric") or 0.0),
                        status_descriptor=row.get("status_descriptor") or "NOMINAL",
                        is_critical_flag=_parse_bool(row.get("is_critical_flag", False)),
                    )
                    dossier = supervisor.process_task(payload)
                except (TypeError, ValueError, SecurityException) as exc:
                    parser.error(f"invalid value on CSV row {row_number}: {exc}")

                result = dict(row)
                result.update(
                    {
                        "overall_urgency": dossier.overall_urgency.value,
                        "integrity_status": dossier.integrity_status.value,
                        "total_alerts": dossier.total_alerts,
                        "audit_hash": dossier.audit_hash,
                    }
                )
                out_rows.append(result)

            with output_path.open(mode="w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=_batch_fieldnames(fieldnames))
                writer.writeheader()
                writer.writerows(out_rows)
            print(f"Processed {len(out_rows)} records -> {output_path}")
            return 0

        if args.command == "serve":
            try:
                import uvicorn
                from agents.api import app
            except ImportError:
                print("Server dependencies are not installed. Run: pip install '.[server]'", file=sys.stderr)
                return 1
            uvicorn.run(app, host=args.host, port=args.port)
            return 0
    except SecurityException as exc:
        print(f"Input rejected: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
