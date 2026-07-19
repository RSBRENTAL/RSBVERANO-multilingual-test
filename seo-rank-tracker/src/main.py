import argparse
from datetime import date
from .connectors import google_search_console, bing_webmaster, google_ai_import
from .reports.export_csv import export as export_csv
from .reports.export_html import export as export_html
from .config import load_queries, language_paths, load_json


def maybe_export(args, rows, path):
    if not args.dry_run:
        export_csv(rows, path)
    return rows

def run_google(args):
    rows = google_search_console.run(dry_run=args.dry_run, period=args.period, start_date=args.start_date, end_date=args.end_date)
    return maybe_export(args, rows, "reports/google-search-console.csv")

def run_bing(args):
    rows = bing_webmaster.run(dry_run=args.dry_run, bing_detailed=args.bing_detailed)
    return maybe_export(args, rows, "reports/bing-webmaster.csv")

def run_import_google_ai(args):
    rows = google_ai_import.run(dry_run=args.dry_run)
    return maybe_export(args, rows, "reports/google-generative-ai.csv")

def run_report(rows=None, dry_run=False):
    rows = rows or []
    if not dry_run:
        export_csv(rows, "reports/latest-report.csv")
        export_html(rows, "reports/latest-report.html")
    return rows

def dry_run_summary(rows):
    active = load_queries(include_inactive=False)
    scenarios = load_json("config/scenarios.json")["scenarios"]
    print(f"dry_run=true active_queries={len(active)} languages={len(language_paths())} scenarios={len(scenarios)} rows={len(rows)}")
    for row in rows:
        print(f"{row['source']} status={row['status']} {row['error']}")

def build_parser():
    parser = argparse.ArgumentParser(description="Independent SEO rank tracker")
    parser.add_argument("command", choices=["google","bing","import-google-ai","report","all"])
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without external connections or report writes")
    parser.add_argument("--period", default="7d", choices=["7d","28d","3m","custom"])
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    parser.add_argument("--bing-detailed", action="store_true", help="Run detailed Bing GetQueryPageStats for each unique active query")
    return parser

def validate_dates(args, parser):
    if args.period == "custom" and (not args.start_date or not args.end_date):
        parser.error("--period custom requires --start-date and --end-date in YYYY-MM-DD format")
    for attr in ["start_date", "end_date"]:
        value = getattr(args, attr)
        if value:
            try:
                date.fromisoformat(value)
            except ValueError:
                parser.error(f"--{attr.replace('_','-')} must use YYYY-MM-DD format")
    if args.start_date and args.end_date and date.fromisoformat(args.start_date) > date.fromisoformat(args.end_date):
        parser.error("--start-date must not be later than --end-date")

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_dates(args, parser)
    rows=[]
    if args.command == "google": rows = run_google(args)
    elif args.command == "bing": rows = run_bing(args)
    elif args.command == "import-google-ai": rows = run_import_google_ai(args)
    elif args.command == "report": rows = run_report([], dry_run=args.dry_run)
    elif args.command == "all":
        rows.extend(run_google(args)); rows.extend(run_bing(args)); rows.extend(run_import_google_ai(args)); run_report(rows, dry_run=args.dry_run)
    if args.dry_run:
        dry_run_summary(rows)
    else:
        print(f"Rows: {len(rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
